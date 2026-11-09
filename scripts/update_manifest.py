#!/usr/bin/env python3
"""Set version / published / size / sha256 / url / changes for one pack.

A pack we built and uploaded (Hosted):

    python scripts/update_manifest.py --id core \
        --file dist/core.hfdb \
        --url https://github.com/Evolvlabsai/holdfast-packs/releases/download/core-2026.11.09/core.hfdb \
        --changes "Shelter list and NOAA radio frequencies refreshed."

A pack we only link to (Linked), re-pointed at a new upstream edition. ``size``
comes from a HEAD and ``sha256`` from the publisher's own ``.sha256`` sidecar,
so nothing large is downloaded and no checksum is ever invented:

    python scripts/update_manifest.py --id shelter-repair \
        --url https://download.kiwix.org/zim/ifixit/ifixit_en_all_2026-03.zim \
        --from-url --record-upstream ifixit_en_all_2026-03.zim \
        --changes "Current Kiwix edition of the iFixit archive."

Rules this script keeps:

* ``version`` must sort strictly higher as an ordinal string than the version it
  replaces, because that is how the app decides an update exists.
* ``size`` and ``sha256`` are measured, fetched from a publisher sidecar, or
  passed explicitly. There is no code path that guesses either.
* the root ``published`` timestamp moves whenever a pack entry changes.
* the manifest is rewritten with the same byte layout every time (two-space
  indent, UTF-8, LF, trailing newline) and any existing ``manifest.json.sig`` is
  deleted, because it no longer covers these bytes. Signing happens only in
  ``publish.yml``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import httpcache, util  # noqa: E402
from holdfast import manifest as mf  # noqa: E402

#: Field order inside a pack entry, matching CatalogParser.Serialize in the app
#: so a hand-edited and a tool-edited manifest look the same in a diff.
FIELD_ORDER = [
    "id",
    "name",
    "group",
    "region",
    "version",
    "published",
    "format",
    "size",
    "sha256",
    "url",
    "mirrors",
    "delta",
    "parts",
    "required",
    "staleAfterDays",
    "license",
    "attribution",
    "changes",
    "minAppVersion",
    "description",
]


def reorder(entry: dict) -> dict:
    ordered = {k: entry[k] for k in FIELD_ORDER if k in entry}
    ordered.update({k: v for k, v in entry.items() if k not in ordered})
    return ordered


def fetch_upstream_facts(url: str) -> tuple[int | None, str | None, list[str]]:
    """(size, sha256, notes) for a URL we do not host: HEAD plus the sidecar."""
    notes: list[str] = []
    head = httpcache.head(url)
    if not head.ok:
        util.fail(f"{url} did not respond to HEAD ({head.error or head.status}); refusing to record it")
    size = head.length
    if size is None:
        notes.append("the server sent no Content-Length; pass --size explicitly")

    sha: str | None = None
    for suffix in (".sha256", ".sha256sum"):
        try:
            text = httpcache.get_text(url + suffix)
        except Exception:  # noqa: BLE001 - absent sidecar is the normal case for most hosts
            continue
        token = (text.strip().split() or [""])[0].lower()
        if mf.SHA256_RE.match(token):
            sha = token
            notes.append(f"sha256 read from the publisher's {suffix} sidecar")
            break

    if sha is None:
        notes.append(
            "no .sha256 sidecar was published, so the checksum stays whatever it was. "
            "Either pass --sha256, or download the file once and pass --file."
        )
    if head.last_modified:
        notes.append(f"upstream Last-Modified {head.last_modified}")
    return size, sha, notes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--id", required=True, help="pack id to update")
    parser.add_argument("--manifest", default=None, help="path to manifest.json (default: repo root)")
    parser.add_argument("--file", default=None, help="the built file; its real size and sha256 are recorded")
    parser.add_argument("--url", default=None, help="new primary download URL")
    parser.add_argument("--from-url", action="store_true", help="take size (HEAD) and sha256 (.sha256 sidecar) from --url")
    parser.add_argument("--size", type=int, default=None, help="size in bytes, when it cannot be measured")
    parser.add_argument("--sha256", default=None, help="lower-case hex sha256, when it cannot be measured")
    parser.add_argument("--version", default=None, help="pack version yyyy.MM.dd (default: today, UTC)")
    parser.add_argument("--published", default=None, help="pack published date yyyy-MM-dd (default: today, UTC)")
    parser.add_argument("--changes", default=None, help="the one-line 'what is new' the update list shows")
    parser.add_argument("--mirror", action="append", default=None, help="replace the mirror list (repeatable)")
    parser.add_argument("--format", default=None, help="pack format: hfdb, pmtiles, zim or gguf")
    parser.add_argument("--min-app-version", default=None, help="raise minAppVersion (do this on any format change)")
    parser.add_argument("--stale-after-days", type=int, default=None)
    parser.add_argument("--license", default=None)
    parser.add_argument("--attribution", default=None)
    parser.add_argument(
        "--record-upstream",
        default=None,
        help="also record this as the current upstream in packs/<id>/pack.meta.json "
        "(currentFile / currentTimestamp / currentBuild, per upstream.kind)",
    )
    parser.add_argument("--allow-same-version", action="store_true", help="permit rewriting an entry without bumping version")
    parser.add_argument("--dry-run", action="store_true", help="print what would change and write nothing")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest) if args.manifest else mf.manifest_path()
    data = mf.load(manifest_path)
    try:
        entry = mf.require(data, args.id)
    except KeyError as exc:
        util.fail(str(exc))

    before = dict(entry)
    notes: list[str] = []

    size: int | None = args.size
    sha: str | None = args.sha256.lower() if args.sha256 else None

    if args.file:
        path = Path(args.file)
        if not path.exists():
            util.fail(f"file not found: {path}")
        measured_size, measured_sha = util.size_and_sha256(path)
        size = size or measured_size
        sha = sha or measured_sha
        notes.append(f"size and sha256 measured from {path}")

    if args.from_url:
        url = args.url or entry.get("url")
        if not url or mf.is_placeholder_url(url):
            util.fail("--from-url needs a real --url (or a real url already in the entry)")
        fetched_size, fetched_sha, fetch_notes = fetch_upstream_facts(url)
        size = size if size is not None else fetched_size
        sha = sha or fetched_sha
        notes.extend(fetch_notes)

    version = args.version or util.version_today()
    old_version = before.get("version", "")
    if version <= old_version and not args.allow_same_version:
        util.fail(
            f"version {version} does not sort higher than the current {old_version}. "
            "The app compares versions as ordinal strings, so an equal or lower value means "
            "no update is offered. Pass --version with a higher date, or --allow-same-version "
            "to correct an entry in place."
        )

    entry["version"] = version
    entry["published"] = args.published or util.iso_date()
    if args.url:
        entry["url"] = args.url
    if size is not None:
        entry["size"] = size
    if sha is not None:
        entry["sha256"] = sha
    if args.changes is not None:
        entry["changes"] = args.changes
    if args.mirror is not None:
        entry["mirrors"] = args.mirror
    if args.format:
        if args.format not in mf.FORMATS:
            util.fail(f"--format must be one of {', '.join(mf.FORMATS)}")
        if args.format != before.get("format") and not args.min_app_version:
            util.fail(
                f"format changes from {before.get('format')!r} to {args.format!r}, so minAppVersion must be "
                "raised in the same edit: an older app cannot read the new file. Pass --min-app-version."
            )
        entry["format"] = args.format
    if args.min_app_version:
        entry["minAppVersion"] = args.min_app_version
    if args.stale_after_days is not None:
        entry["staleAfterDays"] = args.stale_after_days
    if args.license:
        entry["license"] = args.license
    if args.attribution:
        entry["attribution"] = args.attribution

    remaining = mf.placeholder_reasons(entry)
    if remaining:
        notes.append("this entry is STILL a placeholder: " + "; ".join(remaining))

    # Replace the entry in place, keeping pack order stable.
    packs = mf.packs(data)
    index = next(i for i, p in enumerate(packs) if p.get("id") == args.id)
    packs[index] = reorder(entry)
    data["published"] = util.iso_timestamp()

    changed_fields = [
        k for k in set(before) | set(entry) if before.get(k) != entry.get(k)
    ]
    util.info(f"pack {args.id}")
    for field in sorted(changed_fields):
        util.info(f"  {field}: {before.get(field)!r} -> {entry.get(field)!r}")
    if not changed_fields:
        util.info("  (nothing changed)")
    util.info(f"  root published -> {data['published']}")
    for note in notes:
        util.info(f"  · {note}")

    if args.dry_run:
        util.info("")
        util.info("dry run: nothing written")
        return 0

    mf.save(data, manifest_path)
    util.info("")
    util.info(f"wrote {manifest_path}")

    sig = Path(str(manifest_path) + ".sig")
    if sig.exists():
        sig.unlink()
        util.info(f"removed {sig} (it no longer covers these bytes; publish.yml re-signs on main)")

    if args.record_upstream:
        record_upstream(args.id, args.record_upstream)

    return 0


def record_upstream(pack_id: str, value: str) -> None:
    """Remember the edition we just adopted, so the next check compares against it."""
    path = mf.pack_dir(pack_id) / "pack.meta.json"
    if not path.exists():
        util.warn(f"{path} not found; --record-upstream had nothing to update")
        return
    raw = util.read_json(path)
    if not isinstance(raw, dict):
        util.warn(f"{path} is not an object; --record-upstream skipped")
        return
    upstream = raw.setdefault("upstream", {})
    key = {
        "kiwix": "currentFile",
        "geofabrik": "currentTimestamp",
        "protomaps": "currentBuild",
    }.get(upstream.get("kind", ""), "current")
    upstream[key] = value
    util.write_json(path, raw)
    util.info(f"recorded upstream.{key} = {value} in {path}")


if __name__ == "__main__":
    raise SystemExit(main())
