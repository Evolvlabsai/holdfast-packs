#!/usr/bin/env python3
"""Build an ``hfdb`` pack from quick cards, markdown documents and map overlays.

    python scripts/build_core.py --sources packs/core/sources --out dist/core.hfdb

This is the builder for ``core`` and for every other hand-written hfdb pack
(``medical``, ``water-food``, the text half of ``manuals``): pass a different
``--sources`` directory and ``--id``.

Source layout (all three parts optional, but a pack with none is an error):

    <sources>/cards.json          JSON array of quick cards, in Home-grid order
    <sources>/docs/**/*.md        library documents, one file per document
    <sources>/overlays/*.geojson  map overlays, one FeatureCollection per file

Document conventions, identical to ``tools/Holdfast.PackTool build-hfdb`` in the
app repo so a pack built either way is the same pack:

* ``doc_id``   = the file name without its extension (so it must be unique)
* ``title``    = the first ``# `` heading, else the file name
* ``source``   = the first line starting ``Source:`` (dropped from the body)
* ``location`` = the path relative to the docs directory, forward slashes
* ``body``     = everything else, trimmed

Overlays: ``overlay_id`` = file name stem, ``region`` = ``--region`` or guessed
from an id like ``us-md-shelters`` -> ``US-MD``. Every feature must carry
``properties.kind`` in {rally, water, medical, shelter, fuel} and
``properties.name``; the writer rejects the pack otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import hfdb, util  # noqa: E402


def read_markdown(path: Path) -> tuple[str, str | None, str]:
    """(title, source, body) -- see the module docstring for the conventions."""
    title = path.stem
    source: str | None = None
    body: list[str] = []
    title_taken = False

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not title_taken and line.startswith("# "):
            title = line[2:].strip()
            title_taken = True
            continue
        if source is None and line.lower().startswith("source:"):
            source = line[len("source:"):].strip()
            continue
        body.append(line)

    return title, source, "\n".join(body).strip()


def region_from_id(overlay_id: str) -> str:
    """``us-md-shelters`` -> ``US-MD``; anything else has no region."""
    parts = [p for p in overlay_id.split("-") if p]
    if len(parts) >= 2 and len(parts[0]) == 2 and len(parts[1]) == 2:
        return f"{parts[0]}-{parts[1]}".upper()
    return ""


def add_cards(writer: hfdb.HfdbWriter, cards_path: Path, *, allow_draft: bool) -> None:
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    if not isinstance(cards, list):
        util.fail(f"{cards_path}: expected a JSON array of quick cards")

    drafts = []
    for sort, card in enumerate(cards):
        if not isinstance(card, dict):
            util.fail(f"{cards_path}: card at index {sort} is not an object")
        if card.get("draft"):
            drafts.append(card.get("id", f"#{sort}"))
        writer.add_card(card, sort)

    if drafts:
        message = (
            f"{len(drafts)} quick card(s) are marked draft and have not been reviewed: "
            + ", ".join(str(d) for d in drafts)
        )
        if allow_draft:
            util.warn(message + " -- building anyway because --allow-draft was passed")
        else:
            util.fail(
                message
                + ".\nThe spec requires every quick card to cite its source and be reviewed before "
                "release, medical cards ideally by a licensed EMT or nurse. Pass --allow-draft to "
                "build a development pack anyway; never pass it in a release job."
            )


def add_docs(writer: hfdb.HfdbWriter, docs_dir: Path) -> None:
    files = sorted(docs_dir.rglob("*.md"), key=lambda p: str(p).lower())
    if not files:
        util.warn(f"{docs_dir}: no .md files found")

    seen: dict[str, Path] = {}
    for path in files:
        doc_id = path.stem
        if doc_id in seen:
            util.fail(f"duplicate doc_id '{doc_id}': {seen[doc_id]} and {path} (doc_id is the file name stem)")
        seen[doc_id] = path

        title, source, body = read_markdown(path)
        if not body:
            util.warn(f"{path}: document body is empty; it will never match a search")
        location = path.relative_to(docs_dir).as_posix()
        writer.add_document(doc_id, title, body, location, source)


def add_overlays(writer: hfdb.HfdbWriter, overlays: list[Path], region: str | None) -> None:
    for path in overlays:
        overlay_id = path.stem
        writer.add_overlay(overlay_id, region or region_from_id(overlay_id), path.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources", required=True, help="source directory (cards.json, docs/, overlays/)")
    parser.add_argument("--out", required=True, help="output .hfdb path")
    parser.add_argument("--id", default="core", help="pack id written to meta (default: core)")
    parser.add_argument("--name", default=None, help="display name written to meta (default: the id, capitalised)")
    parser.add_argument("--version", default=None, help="pack version yyyy.MM.dd (default: today, UTC)")
    parser.add_argument("--region", default=None, help="region code for overlays, e.g. US-MD")
    parser.add_argument("--cards", default=None, help="override the cards.json path")
    parser.add_argument("--docs", default=None, help="override the docs directory")
    parser.add_argument("--overlays", default=None, help="override the overlays directory or a single .geojson file")
    parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="build even though quick cards are marked \"draft\": true (development only)",
    )
    parser.add_argument("--query", default=None, help="after building, run this search against the pack and print the hits")
    args = parser.parse_args(argv)

    sources = Path(args.sources).resolve()
    if not sources.is_dir():
        util.fail(f"sources directory not found: {sources}")

    cards_path = Path(args.cards) if args.cards else sources / "cards.json"
    docs_dir = Path(args.docs) if args.docs else sources / "docs"
    overlays_arg = Path(args.overlays) if args.overlays else sources / "overlays"

    if overlays_arg.is_dir():
        overlay_files = sorted(overlays_arg.glob("*.geojson"))
    elif overlays_arg.is_file():
        overlay_files = [overlays_arg]
    else:
        overlay_files = []

    if not cards_path.exists() and not docs_dir.is_dir() and not overlay_files:
        util.fail(f"{sources}: nothing to build (no cards.json, no docs/, no overlays/*.geojson)")

    version = args.version or util.version_today()
    name = args.name or args.id.replace("-", " ").capitalize()
    out = Path(args.out)

    with hfdb.HfdbWriter(out, args.id, name, version) as writer:
        if args.region:
            writer.set_meta("region", args.region)
        writer.set_meta("built", util.iso_timestamp())
        writer.set_meta("generator", "holdfast-packs/scripts/build_core.py")

        if cards_path.exists():
            add_cards(writer, cards_path, allow_draft=args.allow_draft)
        if docs_dir.is_dir():
            add_docs(writer, docs_dir)
        if overlay_files:
            add_overlays(writer, overlay_files, args.region)

        docs, cards, overlays = writer.docs, writer.cards, writer.overlays
        writer.complete()

    size, digest = util.size_and_sha256(out)
    util.info(f"wrote {out.resolve()}")
    util.info(
        f"id {args.id} · name {name} · version {version} · "
        f"{docs} doc(s) · {cards} card(s) · {overlays} overlay(s)"
    )
    util.info(f"size   {size} ({util.human_bytes(size)})")
    util.info(f"sha256 {digest}")

    if args.query:
        hits = hfdb.search(out, args.query, limit=5)
        util.info("")
        util.info(f'search "{args.query}" -> {len(hits)} hit(s) (app query path: FTS5 MATCH + bm25)')
        for hit in hits:
            util.info(f"  {hit['score']:.2f}  {hit['title']}  [{hit['location']}]")
            util.info(f"        {hit['snippet'][:120]}")
        if not hits:
            util.fail("the built pack answered the verification query with nothing; the FTS index is wrong")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
