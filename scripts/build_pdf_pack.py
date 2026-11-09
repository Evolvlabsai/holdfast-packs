#!/usr/bin/env python3
"""Download the public-domain PDFs a pack lists, extract their text, build an hfdb.

    python scripts/build_pdf_pack.py --pack manuals --out dist/manuals.hfdb
    python scripts/build_pdf_pack.py --sources packs/manuals/sources.json --out dist/manuals.hfdb

Sources file: ``packs/<id>/sources.json`` (JSON; a sibling ``sources.yaml`` is
accepted only when PyYAML is installed -- JSON is the supported form so the
pipeline needs no YAML parser). Shape:

    {
      "pack": { "id": "manuals", "name": "Survival manuals", "license": "...", "attribution": "..." },
      "documents": [
        {
          "id": "atp-3-50-21",
          "title": "ATP 3-50.21 Survival",
          "url": "https://.../ATP_3-50-21.pdf",
          "source": "US Army Training and Doctrine Command (public domain)",
          "license": "Public domain (US Government work)",
          "verified": false,
          "pages": "all"
        }
      ]
    }

* Downloads are conditional: the ETag / Last-Modified of every URL is cached in
  ``.cache/http.json`` and an unchanged PDF is never fetched again.
* One hfdb document per PDF page, ``location`` = ``"p. N"``, so a search hit can
  cite a page the way the spec requires. ``doc_id`` = ``<id>#p<N>``.
* Pages with no extractable text (scans) are skipped and counted: a pack that is
  mostly scans needs OCR, which this script does not do.
* ``"verified": false`` means nobody has confirmed that URL is the right file
  from the right publisher. The build refuses to run on unverified entries
  unless ``--allow-unverified`` is passed, because a pack is only as
  trustworthy as the documents in it.

Needs ``pypdf`` (see scripts/requirements.txt): permissive licence (BSD-3),
pure Python, no native build in CI.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import hfdb, httpcache, util  # noqa: E402

WHITESPACE_RE = re.compile(r"[ \t ]+")
BLANKLINES_RE = re.compile(r"\n{3,}")


def load_sources(path: Path) -> dict:
    if path.suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import-not-found]
        except ImportError:
            util.fail(
                f"{path} is YAML but PyYAML is not installed. Either `pip install pyyaml` or "
                "convert the file to sources.json (JSON is the supported form)."
            )
        return yaml.safe_load(path.read_text(encoding="utf-8"))  # type: ignore[no-any-return]
    return util.read_json(path)  # type: ignore[return-value]


def clean_text(text: str) -> str:
    """Tidy extracted text: collapse runs of spaces, de-hyphenate line breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = WHITESPACE_RE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return BLANKLINES_RE.sub("\n\n", text).strip()


def parse_page_filter(spec: object, total: int) -> list[int]:
    """``"all"``, ``"1-20"``, ``"3,5,9-12"`` -> a list of 1-based page numbers."""
    if spec in (None, "", "all"):
        return list(range(1, total + 1))
    wanted: list[int] = []
    for part in str(spec).split(","):
        part = part.strip()
        if "-" in part:
            lo, _, hi = part.partition("-")
            wanted.extend(range(int(lo), min(int(hi), total) + 1))
        elif part:
            wanted.append(int(part))
    return [p for p in wanted if 1 <= p <= total]


def extract_pdf(writer: hfdb.HfdbWriter, doc: dict, pdf_path: Path) -> tuple[int, int]:
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError

    doc_id = doc["id"]
    title = doc.get("title") or doc_id
    source = doc.get("source") or doc.get("url")

    try:
        reader = PdfReader(str(pdf_path))
    except PdfReadError as exc:
        util.fail(f"{pdf_path}: not a readable PDF ({exc})")

    if reader.is_encrypted:
        # Many government PDFs carry an owner password with an empty user password.
        try:
            reader.decrypt("")
        except Exception as exc:  # noqa: BLE001 - pypdf raises several types here
            util.fail(f"{pdf_path}: encrypted and cannot be opened ({exc})")

    total = len(reader.pages)
    pages = parse_page_filter(doc.get("pages"), total)
    written = 0
    empty = 0

    for number in pages:
        try:
            text = clean_text(reader.pages[number - 1].extract_text() or "")
        except Exception as exc:  # noqa: BLE001 - a single bad page must not kill the pack
            util.warn(f"{doc_id} p. {number}: text extraction failed ({exc}); page skipped")
            empty += 1
            continue

        if len(text) < 20:
            empty += 1
            continue

        writer.add_document(
            doc_id=f"{doc_id}#p{number}",
            title=f"{title} — p. {number}",
            body=text,
            location=f"p. {number}",
            source=source,
        )
        written += 1

    util.info(f"  {doc_id}: {written} page(s) with text, {empty} skipped, {total} in the file")
    return written, empty


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", default=None, help="pack id; reads packs/<id>/sources.json")
    parser.add_argument("--sources", default=None, help="explicit path to a sources.json / sources.yaml")
    parser.add_argument("--out", required=True, help="output .hfdb path")
    parser.add_argument("--version", default=None, help="pack version yyyy.MM.dd (default: today, UTC)")
    parser.add_argument("--downloads", default=None, help="where to keep the PDFs (default: .cache/pdf/<pack>)")
    parser.add_argument("--cache", default=None, help="HTTP validator cache (default: .cache/http.json)")
    parser.add_argument("--offline", action="store_true", help="use already-downloaded PDFs only; never fetch")
    parser.add_argument(
        "--allow-unverified",
        action="store_true",
        help='build even though some documents are marked "verified": false',
    )
    parser.add_argument("--query", default=None, help="after building, search the pack and print the hits")
    args = parser.parse_args(argv)

    root = util.repo_root()
    if args.sources:
        sources_path = Path(args.sources)
    elif args.pack:
        candidates = [root / "packs" / args.pack / "sources.json", root / "packs" / args.pack / "sources.yaml"]
        sources_path = next((c for c in candidates if c.exists()), candidates[0])
    else:
        util.fail("pass --pack <id> or --sources <file>")

    if not sources_path.exists():
        util.fail(f"sources file not found: {sources_path}")

    data = load_sources(sources_path)
    pack = data.get("pack") or {}
    pack_id = pack.get("id") or args.pack or sources_path.parent.name
    documents = data.get("documents") or []
    if not documents:
        util.fail(f"{sources_path}: no documents listed")

    unverified = [d.get("id", "?") for d in documents if not d.get("verified")]
    if unverified:
        message = (
            f"{len(unverified)} document source URL(s) are not marked verified: "
            + ", ".join(str(u) for u in unverified)
        )
        if args.allow_unverified:
            util.warn(message + " -- building anyway because --allow-unverified was passed")
        else:
            util.fail(
                message
                + f".\nOpen each URL, confirm it is the right edition from the right publisher, then set "
                f'"verified": true in {sources_path}. Pass --allow-unverified for a local trial build.'
            )

    downloads = Path(args.downloads) if args.downloads else root / ".cache" / "pdf" / pack_id
    cache = httpcache.Cache.load(Path(args.cache) if args.cache else root / ".cache" / "http.json")

    out = Path(args.out)
    version = args.version or util.version_today()
    total_pages = 0

    with hfdb.HfdbWriter(out, pack_id, pack.get("name") or pack_id, version) as writer:
        writer.set_meta("built", util.iso_timestamp())
        writer.set_meta("generator", "holdfast-packs/scripts/build_pdf_pack.py")
        if pack.get("license"):
            writer.set_meta("license", pack["license"])
        if pack.get("attribution"):
            writer.set_meta("attribution", pack["attribution"])

        for doc in documents:
            doc_id = doc.get("id")
            url = doc.get("url")
            if not doc_id or not url:
                util.fail(f"{sources_path}: every document needs an 'id' and a 'url' (got {doc!r})")

            local = downloads / (doc.get("file") or f"{doc_id}.pdf")
            if args.offline:
                if not local.exists():
                    util.fail(f"--offline but {local} is not there; run once without --offline")
                util.info(f"{doc_id}: using cached {local.name}")
            else:
                fetched = httpcache.download(url, local, cache=cache)
                util.info(f"{doc_id}: {'downloaded' if fetched else 'unchanged'} {url}")

            written, _ = extract_pdf(writer, doc, local)
            total_pages += written

        writer.complete()

    cache.save()

    if total_pages == 0:
        util.fail(
            "no page produced any text. These PDFs are probably scans; they need OCR, "
            "which this script deliberately does not do."
        )

    size, digest = util.size_and_sha256(out)
    util.info("")
    util.info(f"wrote {out.resolve()}")
    util.info(f"id {pack_id} · version {version} · {total_pages} page document(s)")
    util.info(f"size   {size} ({util.human_bytes(size)})")
    util.info(f"sha256 {digest}")

    if args.query:
        hits = hfdb.search(out, args.query, limit=5)
        util.info("")
        util.info(f'search "{args.query}" -> {len(hits)} hit(s)')
        for hit in hits:
            util.info(f"  {hit['score']:.2f}  {hit['title']}  [{hit['location']}]")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
