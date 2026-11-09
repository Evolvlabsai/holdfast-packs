#!/usr/bin/env python3
"""Ask every upstream whether it has anything new. Download nothing unless it does.

    python scripts/check_upstream.py
    python scripts/check_upstream.py --pack shelter-repair --verbose
    python scripts/check_upstream.py --json-out changes.json --github-output

Prints one line per pack saying ``changed``, ``unchanged``, ``placeholder`` or
``error``, then a summary. Exit code 0 whether or not anything changed (so the
weekly workflow can branch on the output rather than on a failure); exit 1 only
when a check itself broke.

What it checks, per ``packs/<id>/pack.meta.json`` -> ``upstream.kind``:

``kiwix``
    The OPDS catalog on library.kiwix.org, by book name:
    ``/catalog/search?name=<book>&count=10``. A book name carries **no flavour
    suffix** -- ``wikipedia_en_top``, not ``wikipedia_en_top_maxi`` -- and the
    three flavours come back as separate entries distinguished by a
    ``<flavour>`` element, so ``upstream.flavour`` picks one (``maxi``,
    ``nopic``, ``mini``, or absent for a book with a single flavour such as
    ``ifixit_en_all``). The acquisition link points at the **current** edition's
    ``.meta4``; the ``.zim`` URL is the same path without that suffix.
    download.kiwix.org publishes no undated "latest" alias and its HTML listings
    hide the checksum siblings, so the catalog is the only honest way to resolve
    "newest". Changed = the resolved file name differs from
    ``upstream.currentFile``.

    The catalog's ``length`` attribute is rounded **up** to a 512-byte boundary
    (296,858,624 for a file of 296,858,160 bytes), so it is reported here as a
    hint and never written to the manifest. ``update_manifest.py --from-url``
    takes the real size from a HEAD.

``geofabrik``
    ``<path>-updates/state.txt``, whose ``timestamp=`` is the cut-off of the
    published extract (plus the ``.osm.pbf``'s own Last-Modified as a fallback).
    Changed = a newer timestamp than ``upstream.currentTimestamp``.

``protomaps``
    ``https://build-metadata.protomaps.dev/builds.json``, the index of daily
    planet builds. Changed = a newer build date than ``upstream.currentBuild``.
    (The bucket root has no listing and there is no ``latest`` alias.)

``pdfs``
    A HEAD per URL in ``packs/<id>/sources.json``, compared against the ETag /
    Last-Modified remembered in ``.cache/http.json``. Not one byte of PDF is
    fetched. Changed = any validator moved. First run has nothing to compare
    against and reports ``unknown`` rather than pretending.

``manual``
    Never changes by itself; reports its note. For packs a human releases
    deliberately (the AI model).

Nothing here writes to the manifest. ``update_manifest.py`` does that, after a
rebuild, and only in a pull request.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# The OPDS feed is data from a third party, so it is parsed with defusedxml
# rather than xml.etree: no external entities, no entity expansion.
import defusedxml.ElementTree as ET
from xml.etree.ElementTree import ParseError

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import httpcache, util  # noqa: E402
from holdfast import manifest as mf  # noqa: E402

KIWIX_SEARCH = "https://library.kiwix.org/catalog/search?name={book}&count=10"
GEOFABRIK_BASE = "https://download.geofabrik.de/{path}"
PROTOMAPS_BUILDS = "https://build-metadata.protomaps.dev/builds.json"

ATOM = "{http://www.w3.org/2005/Atom}"
TIMESTAMP_RE = re.compile(r"^timestamp\s*=\s*(.+)$", re.MULTILINE)
SEQUENCE_RE = re.compile(r"^sequenceNumber\s*=\s*(\d+)$", re.MULTILINE)

CHANGED = "changed"
UNCHANGED = "unchanged"
UNKNOWN = "unknown"
PLACEHOLDER = "placeholder"
ERROR = "error"


@dataclass
class Check:
    pack_id: str
    kind: str
    state: str
    detail: str = ""
    current: str | None = None
    latest: str | None = None
    url: str | None = None
    size: int | None = None
    sha256: str | None = None
    notes: list[str] = field(default_factory=list)

    def to_json(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if v not in (None, "", [])}


# -- Kiwix -----------------------------------------------------------------


def check_kiwix(pack_id: str, up: dict, *, verbose: bool) -> Check:
    book = up.get("book")
    if not book:
        return Check(pack_id, "kiwix", ERROR, "upstream.book is missing from pack.meta.json")

    wanted_flavour = (up.get("flavour") or "").strip()
    url = KIWIX_SEARCH.format(book=book)
    try:
        xml = httpcache.get_text(url)
    except Exception as exc:  # noqa: BLE001 - any failure to reach the catalog reads the same
        return Check(pack_id, "kiwix", ERROR, f"could not read {url}: {exc}")

    try:
        root = ET.fromstring(xml)
    except ParseError as exc:
        return Check(pack_id, "kiwix", ERROR, f"{url} did not return parseable OPDS: {exc}")

    entries = root.findall(f"{ATOM}entry")
    if not entries:
        return Check(
            pack_id,
            "kiwix",
            ERROR,
            f"the catalog knows no book named '{book}'. Book names carry no flavour suffix: "
            "use 'wikipedia_en_top' with flavour 'maxi', not 'wikipedia_en_top_maxi'.",
        )

    flavours = []
    entry = None
    for candidate in entries:
        flavour_el = candidate.find(f"{ATOM}flavour")
        flavour = (flavour_el.text or "").strip() if flavour_el is not None else ""
        flavours.append(flavour or "(none)")
        if flavour == wanted_flavour:
            entry = candidate
            break

    if entry is None:
        return Check(
            pack_id,
            "kiwix",
            ERROR,
            f"'{book}' has no flavour {wanted_flavour!r}; the catalog offers {', '.join(flavours)}",
        )

    zim_url: str | None = None
    length: int | None = None
    for link in entry.iter(f"{ATOM}link"):
        href = link.get("href") or ""
        if href.endswith(".meta4") or href.endswith(".zim"):
            zim_url = href.removesuffix(".meta4")
            raw_len = link.get("length")
            if raw_len and raw_len.isdigit():
                # Rounded up to 512 bytes by the catalog: a hint, never the manifest's size.
                length = int(raw_len)
            break

    if not zim_url:
        return Check(pack_id, "kiwix", ERROR, f"the catalog entry for '{book}' carries no download link")

    filename = zim_url.rsplit("/", 1)[-1]
    current = up.get("currentFile")

    # Prefer the stable download.kiwix.org host over whichever mirror the
    # catalog resolved to: the manifest url should not pin one mirror.
    canonical = re.sub(r"^https://[^/]*download\.kiwix\.org/", "https://download.kiwix.org/", zim_url)

    check = Check(
        pack_id,
        "kiwix",
        CHANGED if (current and filename != current) else (UNCHANGED if current else UNKNOWN),
        detail=f"{current or '(nothing recorded)'} -> {filename}" if filename != current else filename,
        current=current,
        latest=filename,
        url=canonical,
        size=length,
    )
    if verbose and check.state == CHANGED:
        head = httpcache.head(canonical)
        if head.ok:
            check.size = head.length or check.size
        sha = fetch_sidecar_sha256(canonical)
        if sha:
            check.sha256 = sha
            check.notes.append("sha256 read from the published .zim.sha256 sidecar")
    return check


def fetch_sidecar_sha256(zim_url: str) -> str | None:
    """Kiwix publishes ``<file>.sha256`` beside every ZIM, though the HTML listing hides it."""
    try:
        text = httpcache.get_text(zim_url + ".sha256")
    except Exception:  # noqa: BLE001 - a missing sidecar is normal enough
        return None
    token = text.strip().split()[0] if text.strip() else ""
    return token.lower() if mf.SHA256_RE.match(token.lower()) else None


# -- Geofabrik -------------------------------------------------------------


def check_geofabrik(pack_id: str, up: dict) -> Check:
    path = up.get("path")  # e.g. north-america/us/maryland
    if not path:
        return Check(pack_id, "geofabrik", ERROR, "upstream.path is missing from pack.meta.json")

    state_url = GEOFABRIK_BASE.format(path=f"{path}-updates/state.txt")
    pbf_url = GEOFABRIK_BASE.format(path=f"{path}-latest.osm.pbf")

    try:
        text = httpcache.get_text(state_url)
    except Exception as exc:  # noqa: BLE001
        return Check(pack_id, "geofabrik", ERROR, f"could not read {state_url}: {exc}")

    match = TIMESTAMP_RE.search(text)
    if not match:
        return Check(pack_id, "geofabrik", ERROR, f"{state_url} has no timestamp= line")

    # state.txt escapes the colons: 2026-11-08T21\:21\:00Z
    latest = match.group(1).strip().replace("\\:", ":")
    sequence = SEQUENCE_RE.search(text)
    current = up.get("currentTimestamp")

    head = httpcache.head(pbf_url)
    check = Check(
        pack_id,
        "geofabrik",
        CHANGED if (current and latest != current) else (UNCHANGED if current else UNKNOWN),
        detail=f"{current or '(nothing recorded)'} -> {latest}" if latest != current else latest,
        current=current,
        latest=latest,
        url=pbf_url,
        size=head.length,
    )
    if sequence:
        check.notes.append(f"sequenceNumber {sequence.group(1)}")
    if not head.ok:
        check.notes.append(f"the .osm.pbf itself did not respond: {head.error}")
    check.notes.append("Geofabrik publishes .osm.pbf.md5 only; there is no sha256 sidecar")
    return check


# -- Protomaps -------------------------------------------------------------


def check_protomaps(pack_id: str, up: dict) -> Check:
    try:
        builds = json.loads(httpcache.get_text(PROTOMAPS_BUILDS))
    except Exception as exc:  # noqa: BLE001
        return Check(pack_id, "protomaps", ERROR, f"could not read {PROTOMAPS_BUILDS}: {exc}")

    dates = sorted(
        {
            str(b.get("key", "")).removesuffix(".pmtiles")
            for b in builds
            if str(b.get("key", "")).endswith(".pmtiles") and str(b.get("key", ""))[:8].isdigit()
        }
    )
    if not dates:
        return Check(pack_id, "protomaps", ERROR, "the build index listed no .pmtiles builds")

    latest = dates[-1][:8]
    current = up.get("currentBuild")
    return Check(
        pack_id,
        "protomaps",
        CHANGED if (current and latest != current) else (UNCHANGED if current else UNKNOWN),
        detail=f"{current or '(nothing recorded)'} -> {latest}" if latest != current else latest,
        current=current,
        latest=latest,
        url=f"https://build.protomaps.com/{latest}.pmtiles",
        notes=["a per-state extract is built from this planet build; see scripts/extract_maps.py"],
    )


# -- PDFs ------------------------------------------------------------------


def check_pdfs(pack_id: str, cache: httpcache.Cache, *, root: Path) -> Check:
    sources = root / "packs" / pack_id / "sources.json"
    if not sources.exists():
        return Check(pack_id, "pdfs", ERROR, f"{sources} not found")

    documents = (util.read_json(sources) or {}).get("documents") or []  # type: ignore[union-attr]
    if not documents:
        return Check(pack_id, "pdfs", ERROR, f"{sources} lists no documents")

    moved: list[str] = []
    first_seen: list[str] = []
    broken: list[str] = []

    for doc in documents:
        url = doc.get("url")
        doc_id = doc.get("id", url)
        if not url:
            broken.append(f"{doc_id}: no url")
            continue
        head = httpcache.head(url)
        if not head.ok:
            broken.append(f"{doc_id}: {head.error or f'HTTP {head.status}'}")
            continue
        verdict = cache.changed(url, head)
        if verdict is None:
            first_seen.append(f"{doc_id} ({head.validator() or 'no validator'})")
        elif verdict:
            moved.append(f"{doc_id} ({head.validator()})")
        cache.remember(url, etag=head.etag, last_modified=head.last_modified, length=head.length)

    state = CHANGED if moved else (ERROR if broken and not first_seen else (UNKNOWN if first_seen else UNCHANGED))
    detail_parts = []
    if moved:
        detail_parts.append(f"{len(moved)} changed: " + ", ".join(moved))
    if first_seen:
        detail_parts.append(f"{len(first_seen)} not seen before: " + ", ".join(first_seen))
    if broken:
        detail_parts.append(f"{len(broken)} unreachable: " + ", ".join(broken))

    check = Check(pack_id, "pdfs", state, "; ".join(detail_parts) or f"{len(documents)} document(s) unchanged")
    if broken:
        check.notes.append("an unreachable source URL needs a new link or a mirror before the next build")
    return check


# -- driver ----------------------------------------------------------------


def run_checks(pack_ids: list[str] | None, *, root: Path, verbose: bool) -> list[Check]:
    metas = mf.all_pack_metas(root)
    data = mf.load(mf.manifest_path(root)) if mf.manifest_path(root).exists() else {"packs": []}
    cache = httpcache.Cache.load(root / ".cache" / "http.json")
    checks: list[Check] = []

    for pack_id, meta in metas.items():
        if pack_ids and pack_id not in pack_ids:
            continue
        up = meta.upstream or {}
        kind = up.get("kind", "manual")

        if kind == "kiwix":
            check = check_kiwix(pack_id, up, verbose=verbose)
        elif kind == "geofabrik":
            check = check_geofabrik(pack_id, up)
        elif kind == "protomaps":
            check = check_protomaps(pack_id, up)
        elif kind == "pdfs":
            check = check_pdfs(pack_id, cache, root=root)
        elif kind == "manual":
            check = Check(pack_id, "manual", UNCHANGED, up.get("notes") or "released by hand only")
        elif kind == "none":
            check = Check(pack_id, "none", UNCHANGED, up.get("notes") or "no upstream; content is written in this repo")
        else:
            check = Check(pack_id, kind, ERROR, f"unknown upstream.kind '{kind}'")

        entry = mf.find(data, pack_id)
        if entry is not None and mf.is_placeholder(entry):
            check.notes.append("the manifest entry is still a placeholder: " + "; ".join(mf.placeholder_reasons(entry)))
            if check.state == UNCHANGED:
                check.state = PLACEHOLDER
        checks.append(check)

    cache.save()
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", action="append", default=None, help="only this pack id (repeatable)")
    parser.add_argument("--json-out", default=None, help="write the full result as JSON here")
    parser.add_argument(
        "--github-output",
        action="store_true",
        help="append changed=<true|false> and changed_packs=<csv> to $GITHUB_OUTPUT",
    )
    parser.add_argument("--verbose", action="store_true", help="also resolve size and sha256 for changed Kiwix books")
    args = parser.parse_args(argv)

    root = util.repo_root()
    checks = run_checks(args.pack, root=root, verbose=args.verbose)
    if not checks:
        util.fail("no packs to check (is packs/<id>/pack.meta.json missing?)")

    width = max(len(c.pack_id) for c in checks)
    for check in checks:
        util.info(f"{check.pack_id.ljust(width)}  {check.state.upper():<11} [{check.kind}] {check.detail}")
        for note in check.notes:
            util.info(f"{' ' * width}  · {note}")

    changed = [c.pack_id for c in checks if c.state == CHANGED]
    errors = [c.pack_id for c in checks if c.state == ERROR]
    unknown = [c.pack_id for c in checks if c.state == UNKNOWN]

    util.info("")
    util.info(
        f"{len(changed)} changed, {len(checks) - len(changed) - len(errors) - len(unknown)} unchanged, "
        f"{len(unknown)} unknown (nothing recorded yet), {len(errors)} error"
    )
    if changed:
        util.info("changed: " + ", ".join(changed))
    if unknown:
        util.info(
            "unknown: " + ", ".join(unknown) + " -- record the current upstream in "
            "packs/<id>/pack.meta.json so the next run can compare"
        )
    if errors:
        util.info("errors:  " + ", ".join(errors))
    util.info("Nothing was downloaded." if not args.verbose else "No pack file was downloaded.")

    if args.json_out:
        util.write_json(args.json_out, {"checks": [c.to_json() for c in checks], "changed": changed, "errors": errors})
        util.info(f"wrote {args.json_out}")

    if args.github_output:
        path = os.environ.get("GITHUB_OUTPUT")
        if not path:
            util.warn("--github-output but $GITHUB_OUTPUT is not set")
        else:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(f"changed={'true' if changed else 'false'}\n")
                fh.write(f"changed_packs={','.join(changed)}\n")
                fh.write(f"errors={','.join(errors)}\n")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
