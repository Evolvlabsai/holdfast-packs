#!/usr/bin/env python3
"""Build ``news.json`` (the "News & tips" feed) from ``news/items/*.json``.

    python scripts/build_news.py            # validate every item and write news.json
    python scripts/build_news.py --check    # validate, and fail if news.json is not what the sources build

Every item is checked against ``schema/news.schema.json`` and the rules a
schema cannot express (unique ids, real dates, body formatting, image limits).
Image ``sha256``, ``size``, ``width`` and ``height`` are computed here from
``news/img/<file>``; they are never typed by hand. Items are sorted newest
first, and only the newest 50 are kept.

The output depends on the sources alone -- not on the clock, the machine or the
order files are listed in -- so ``publish.yml`` can run ``--check`` and sign the
committed bytes knowing they are exactly what these sources produce.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import news, util  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=None, help="folder holding news/ (default: the repo root)")
    parser.add_argument("--out", default=None, help="where to write the feed (default: <root>/news.json)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="write nothing; exit 1 unless the existing feed is byte-for-byte what the sources build",
    )
    args = parser.parse_args(argv)

    root = Path(args.root) if args.root else None
    out = Path(args.out) if args.out else news.news_path(root)

    try:
        result = news.build(root, today=util.today())
    except news.NewsError as exc:
        for problem in exc.problems:
            print(f"error: {problem}", file=sys.stderr)
        print(f"error: {len(exc.problems)} problem(s); news.json was not written", file=sys.stderr)
        return 1

    for warning in result.warnings:
        util.warn(warning)
    if result.dropped:
        util.info(f"keeping the newest {news.MAX_ITEMS}; dropped {len(result.dropped)}: {', '.join(result.dropped)}")

    expected = news.canonical_bytes(result.feed)
    items = result.feed["items"]
    if args.check:
        if not out.exists():
            print(f"error: {out} does not exist; run scripts/build_news.py", file=sys.stderr)
            return 1
        if out.read_bytes() != expected:
            print(
                f"error: {out} is not what news/items builds; run scripts/build_news.py and commit the result",
                file=sys.stderr,
            )
            return 1
        util.info(f"{out.name} is up to date: {len(items)} item(s), {len(expected)} bytes, published {result.feed['published']}")
        return 0

    changed = not out.exists() or out.read_bytes() != expected
    news.write(result.feed, out)
    util.info(f"wrote {out} ({len(items)} item(s), {len(expected)} bytes, published {result.feed['published']})")
    # Like update_manifest.py: a signature over the old bytes would look forged.
    stale = Path(str(out) + ".sig")
    if changed and stale.exists():
        stale.unlink()
        util.info(f"deleted stale {stale}; publish.yml signs the new bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
