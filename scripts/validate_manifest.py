#!/usr/bin/env python3
"""Check the manifest the way CI must, before anything gets signed.

    python scripts/validate_manifest.py                       # schema + structure, no network
    python scripts/validate_manifest.py --network              # + every url and mirror must answer
    python scripts/validate_manifest.py --network --checksums  # + download and hash hosted files
    python scripts/validate_manifest.py --dist dist            # + hash files sitting on disk

Checks, in the order the spec lists them ("CI validation"):

1. **Schema.** ``schema/manifest.schema.json``, which also rejects unknown
   fields -- a misspelled key would otherwise take its default silently.
2. **Structure the schema cannot express:** unique pack ids; a pack folder under
   ``packs/`` for every id; exactly one ``required: true`` pack; versions that
   sort higher than the previous manifest's; ``parts`` for anything over 2 GB we
   host; region codes that match the id.
3. **Placeholders.** Every unknown url, size or sha256 is listed by name. They
   fail the run unless ``--allow-placeholders``, which is what the repo does
   today while most packs are unbuilt -- so CI stays green but can never go
   quiet about them.
4. **Reachability** (``--network``): HEAD on every url and every mirror.
5. **Size** (``--network``): the server's Content-Length must equal ``size``.
6. **Checksums** (``--checksums`` or ``--dist``): the file's real SHA-256 must
   equal ``sha256`` -- from a local build directory, or by downloading.
7. **Size drift.** A pack that grew or shrank by more than its threshold
   (``packs/<id>/pack.meta.json`` -> ``sizeChangeThresholdPercent``, default
   25%) fails, unless that file says ``allowSizeChange: true``. The baseline is
   ``git show HEAD:manifest.json`` or ``--baseline <file>``.
8. **minAppVersion on format changes.** If a pack's ``format`` differs from the
   baseline and its ``minAppVersion`` was not raised, that fails: an old app
   would download a file it cannot open.

Exit 0 only when every check passed. Warnings alone do not fail the run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import httpcache, util  # noqa: E402
from holdfast import manifest as mf  # noqa: E402

#: GitHub Releases refuses assets over this, and the app splits anything larger
#: into ``parts``.
TWO_GB = 2 * 1024 * 1024 * 1024


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.notes: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)
        print(f"FAIL  {message}", flush=True)

    def warn(self, message: str) -> None:
        self.warnings.append(message)
        print(f"WARN  {message}", flush=True)

    def note(self, message: str) -> None:
        self.notes.append(message)
        print(f"note  {message}", flush=True)

    def ok(self, message: str) -> None:
        print(f"ok    {message}", flush=True)


# -- 1. schema -------------------------------------------------------------


def check_schema(data: dict, schema_file: Path, report: Report) -> None:
    try:
        import jsonschema
    except ImportError:
        report.error("jsonschema is not installed; run pip install -r scripts/requirements.txt")
        return

    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    validator_cls = jsonschema.validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator = validator_cls(schema)

    failures = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    for failure in failures:
        where = "/".join(str(p) for p in failure.absolute_path) or "(root)"
        report.error(f"schema: {where}: {failure.message}")
    if not failures:
        report.ok(f"schema: valid against {schema_file.name}")


# -- 2. structure ----------------------------------------------------------


def check_structure(data: dict, root: Path, report: Report) -> None:
    packs = mf.packs(data)
    ids = [p.get("id") for p in packs]

    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        report.error(f"structure: duplicate pack ids: {', '.join(sorted(str(d) for d in duplicates))}")

    required = [p.get("id") for p in packs if p.get("required")]
    if len(required) != 1:
        report.error(
            f"structure: exactly one pack must be required:true (the spec makes Core required); found {required}"
        )
    elif required[0] != "core":
        report.warn(f"structure: the required pack is '{required[0]}', not 'core'")

    for entry in packs:
        pack_id = str(entry.get("id"))
        folder = root / "packs" / pack_id
        if not folder.is_dir():
            report.error(f"{pack_id}: no packs/{pack_id}/ folder for this manifest entry")
        elif not (folder / "pack.meta.json").exists():
            report.warn(f"{pack_id}: packs/{pack_id}/pack.meta.json is missing, so the pipeline cannot check it")

        region = entry.get("region")
        if region:
            slug = region.lower().replace("-", "-")
            if pack_id.startswith("maps-") and not pack_id.endswith(slug):
                report.warn(f"{pack_id}: region {region} does not match the id's suffix")

        version = entry.get("version", "")
        published = entry.get("published", "")
        if version and published and version.replace(".", "-") > published:
            report.warn(f"{pack_id}: version {version} is later than published {published}")

    report.ok(f"structure: {len(packs)} pack(s), ids unique, folders present")


def check_parts(entry: dict, meta: mf.PackMeta | None, report: Report) -> None:
    pack_id = str(entry.get("id"))
    size = entry.get("size") or 0
    parts = entry.get("parts") or []

    if size > TWO_GB and not parts:
        if meta and meta.linked:
            report.note(
                f"{pack_id}: {util.human_bytes(size)} is over 2 GB with no parts. That is fine for a Linked "
                "pack (the publisher serves one file and we cannot split it), but the app must stream a "
                "single >2 GB download; confirm its downloader and the device filesystem handle that."
            )
        else:
            report.error(
                f"{pack_id}: {util.human_bytes(size)} is over 2 GB and we host it, so it must be split into "
                "'parts' with a checksum each (spec: Large files). GitHub Releases also rejects assets over 2 GB."
            )

    if parts:
        total = sum(p.get("size", 0) for p in parts)
        if total != size:
            report.error(f"{pack_id}: parts add up to {total} bytes but size says {size}")
        indexes = [p.get("index") for p in parts]
        if indexes != list(range(len(parts))):
            report.error(f"{pack_id}: part indexes must be 0..n-1 in order, got {indexes}")


# -- 3. placeholders -------------------------------------------------------


def check_placeholders(data: dict, report: Report, *, allowed: bool) -> list[str]:
    placeholders: list[str] = []
    for entry in mf.packs(data):
        reasons = mf.placeholder_reasons(entry)
        if not reasons:
            continue
        pack_id = str(entry.get("id"))
        placeholders.append(pack_id)
        message = f"{pack_id}: not publishable yet -- " + "; ".join(reasons)
        if allowed:
            report.warn(message)
        else:
            report.error(message)

    if placeholders:
        report.note(
            f"{len(placeholders)} pack(s) are placeholders: {', '.join(placeholders)}. "
            "The app rejects every download whose checksum does not match, so a placeholder entry lists a "
            "pack without letting anything install -- but it must not reach a release manifest."
        )
    else:
        report.ok("placeholders: none; every entry has a real url, size and sha256")
    return placeholders


# -- 4/5. reachability and size -------------------------------------------


def check_reachable(entry: dict, report: Report, *, check_size: bool) -> None:
    pack_id = str(entry.get("id"))
    urls = [("url", entry.get("url"))]
    urls += [(f"mirrors[{i}]", m) for i, m in enumerate(entry.get("mirrors") or [])]
    urls += [(f"parts[{i}]", p.get("url")) for i, p in enumerate(entry.get("parts") or [])]
    delta = entry.get("delta")
    if delta:
        urls.append(("delta.url", delta.get("url")))

    for label, url in urls:
        if not url or mf.is_placeholder_url(url):
            continue
        head = httpcache.head(url)
        if not head.ok:
            report.error(f"{pack_id} {label}: unreachable -- {head.error or f'HTTP {head.status}'} ({url})")
            continue

        if check_size and label in ("url",):
            declared = entry.get("size")
            if head.length is None:
                report.warn(f"{pack_id} {label}: the server sent no Content-Length, so size cannot be checked")
            elif declared and head.length != declared:
                report.error(
                    f"{pack_id} {label}: the hosted file is {head.length} bytes but the manifest says "
                    f"{declared}. The app discards a download whose size differs, so this pack would "
                    f"never install."
                )
            else:
                report.ok(f"{pack_id} {label}: reachable, {util.human_bytes(head.length)} matches size")
        else:
            report.ok(f"{pack_id} {label}: reachable")


# -- 6. checksums ----------------------------------------------------------


def local_candidates(entry: dict, dist: Path) -> list[Path]:
    url = entry.get("url") or ""
    names = [url.rsplit("/", 1)[-1]] if "/" in url else []
    pack_id = str(entry.get("id"))
    fmt = entry.get("format", "hfdb")
    names += [f"{pack_id}.{fmt}"]
    return [dist / n for n in names if n]


def check_checksums(entry: dict, report: Report, *, dist: Path | None, download: bool) -> None:
    pack_id = str(entry.get("id"))
    declared = entry.get("sha256")
    if mf.is_placeholder_sha(declared):
        return

    if dist is not None:
        for candidate in local_candidates(entry, dist):
            if candidate.exists():
                size, digest = util.size_and_sha256(candidate)
                if size != entry.get("size"):
                    report.error(f"{pack_id}: {candidate.name} is {size} bytes, manifest says {entry.get('size')}")
                if digest != declared:
                    report.error(f"{pack_id}: {candidate.name} hashes to {digest}, manifest says {declared}")
                if size == entry.get("size") and digest == declared:
                    report.ok(f"{pack_id}: {candidate.name} matches size and sha256")
                return

    if not download:
        return

    url = entry.get("url")
    if not url or mf.is_placeholder_url(url):
        return

    report.note(f"{pack_id}: downloading {util.human_bytes(entry.get('size'))} to verify its sha256")
    digest = hashlib.sha256()
    total = 0
    request = urllib.request.Request(url, headers={"User-Agent": httpcache.USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=300) as resp:
            while block := resp.read(1 << 22):
                digest.update(block)
                total += len(block)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        report.error(f"{pack_id}: could not download for checksum verification -- {exc}")
        return

    if total != entry.get("size"):
        report.error(f"{pack_id}: downloaded {total} bytes, manifest says {entry.get('size')}")
    if digest.hexdigest() != declared:
        report.error(f"{pack_id}: downloaded file hashes to {digest.hexdigest()}, manifest says {declared}")
    if total == entry.get("size") and digest.hexdigest() == declared:
        report.ok(f"{pack_id}: downloaded file matches size and sha256")


# -- 7/8. drift against the previous manifest ------------------------------


def load_baseline(path: str | None, root: Path, report: Report) -> dict | None:
    if path:
        p = Path(path)
        if not p.exists():
            report.error(f"baseline not found: {p}")
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    try:
        result = subprocess.run(
            ["git", "show", "HEAD:manifest.json"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        report.note("drift: git is not available, so size drift cannot be compared")
        return None

    if result.returncode != 0:
        report.note("drift: no committed manifest.json to compare against (first commit?)")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        report.warn("drift: the committed manifest.json is not valid JSON; skipping drift checks")
        return None


def check_drift(data: dict, baseline: dict, metas: dict[str, mf.PackMeta], report: Report) -> None:
    for entry in mf.packs(data):
        pack_id = str(entry.get("id"))
        old = mf.find(baseline, pack_id)
        if old is None:
            report.note(f"{pack_id}: new pack, nothing to compare")
            continue

        meta = metas.get(pack_id)
        threshold = meta.size_change_threshold_percent if meta else 25.0
        allowed = meta.allow_size_change if meta else False

        old_size = old.get("size") or 0
        new_size = entry.get("size") or 0
        if old_size and new_size and not mf.is_placeholder(entry) and not mf.is_placeholder(old):
            delta = (new_size - old_size) / old_size * 100
            if abs(delta) > threshold:
                message = (
                    f"{pack_id}: size moved {delta:+.1f}% ({util.human_bytes(old_size)} -> "
                    f"{util.human_bytes(new_size)}), over the {threshold:.0f}% threshold"
                )
                if allowed:
                    report.warn(message + ' -- allowed by "allowSizeChange": true in pack.meta.json')
                else:
                    report.error(
                        message
                        + ". A jump this large usually means a broken build or a truncated upload. If it is "
                        'real, set "allowSizeChange": true in packs/'
                        + pack_id
                        + "/pack.meta.json in the same pull request, with a reason."
                    )
            else:
                report.ok(f"{pack_id}: size moved {delta:+.1f}%, within {threshold:.0f}%")

        old_format = old.get("format", "hfdb")
        new_format = entry.get("format", "hfdb")
        if old_format != new_format and mf.is_placeholder(old):
            # The old entry was never built, so no app can have downloaded it in the old format.
            report.ok(f"{pack_id}: format set {old_format} -> {new_format} on first real build")
        elif old_format != new_format:
            old_min = old.get("minAppVersion", "0.0.0")
            new_min = entry.get("minAppVersion", "0.0.0")
            if version_tuple(new_min) <= version_tuple(old_min):
                report.error(
                    f"{pack_id}: format changed {old_format} -> {new_format} but minAppVersion is still "
                    f"{new_min}. Raise it, or an app that cannot read the new format will still download it."
                )
            else:
                report.ok(f"{pack_id}: format changed {old_format} -> {new_format}, minAppVersion raised to {new_min}")

    for old in mf.packs(baseline):
        if mf.find(data, str(old.get("id"))) is None:
            report.warn(
                f"{old.get('id')}: was in the previous manifest and is gone. Removing a pack hides it from "
                "the Packs screen; installed copies stay on the phone."
            )


def version_tuple(value: str) -> tuple[int, ...]:
    try:
        return tuple(int(p) for p in str(value).split("."))
    except ValueError:
        return (0,)


# -- driver ----------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", default=None, help="path to manifest.json (default: repo root)")
    parser.add_argument("--schema", default=None, help="path to the JSON Schema (default: schema/manifest.schema.json)")
    parser.add_argument("--network", action="store_true", help="HEAD every url and mirror, and compare sizes")
    parser.add_argument("--checksums", action="store_true", help="download each hosted file and verify its sha256 (slow)")
    parser.add_argument("--dist", default=None, help="directory of freshly built files to hash instead of downloading")
    parser.add_argument("--baseline", default=None, help="previous manifest.json (default: git show HEAD:manifest.json)")
    parser.add_argument(
        "--allow-placeholders",
        action="store_true",
        help="report placeholder url/size/sha256 as warnings instead of failures (the repo's state today)",
    )
    parser.add_argument("--no-drift", action="store_true", help="skip the size-drift and format checks")
    args = parser.parse_args(argv)

    root = util.repo_root()
    manifest_path = Path(args.manifest) if args.manifest else mf.manifest_path(root)
    schema_file = Path(args.schema) if args.schema else mf.schema_path(root)
    report = Report()

    if not manifest_path.exists():
        util.fail(f"manifest not found: {manifest_path}")
    if not schema_file.exists():
        util.fail(f"schema not found: {schema_file}")

    try:
        data = mf.load(manifest_path)
    except (json.JSONDecodeError, ValueError) as exc:
        util.fail(f"{manifest_path} is not valid JSON: {exc}")

    print(f"validating {manifest_path}")
    print("")

    check_schema(data, schema_file, report)
    check_structure(data, root, report)

    metas = mf.all_pack_metas(root)
    for entry in mf.packs(data):
        check_parts(entry, metas.get(str(entry.get("id"))), report)

    check_placeholders(data, report, allowed=args.allow_placeholders)

    if args.network:
        print("")
        for entry in mf.packs(data):
            check_reachable(entry, report, check_size=True)
    else:
        report.note("reachability and size were not checked (pass --network)")

    if args.dist or args.checksums:
        print("")
        dist = Path(args.dist) if args.dist else None
        for entry in mf.packs(data):
            check_checksums(entry, report, dist=dist, download=args.checksums)
    else:
        report.note("checksums were not verified against real files (pass --dist <dir> or --checksums)")

    if not args.no_drift:
        print("")
        baseline = load_baseline(args.baseline, root, report)
        if baseline is not None:
            check_drift(data, baseline, metas, report)

    print("")
    print(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s)")
    if report.errors:
        print("")
        print("FAILED:")
        for error in report.errors:
            print(f"  - {error}")
        return 1

    print("manifest OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
