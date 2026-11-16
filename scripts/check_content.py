#!/usr/bin/env python3
"""Check every quick card and survival skill against the format in CONTRIBUTING.md.

    python scripts/check_content.py                 # check, list drafts
    python scripts/check_content.py --cards-json dist/cards.json --skills-json dist/skills.json
                                                    # also export both for PackTool

Exits 1 with one plain sentence per problem. Drafts are allowed here (a pull
request starts as a draft); the tests and the pack build refuse them on main.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import content, util  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    root = util.repo_root()
    parser.add_argument("--cards", default=str(root / "packs" / "core" / "sources" / "cards"))
    parser.add_argument("--skills", default=str(root / "packs" / "core" / "sources" / "skills"))
    parser.add_argument("--cards-json", default=None,
                        help="write the reviewed cards here as a JSON array (input for the app's PackTool)")
    parser.add_argument("--skills-json", default=None,
                        help="write the reviewed skills here as a JSON array, drawings inline (input for PackTool)")
    parser.add_argument("--allow-draft", action="store_true",
                        help="include drafts in --cards-json and --skills-json (development only)")
    args = parser.parse_args(argv)

    try:
        cards = content.load_cards(Path(args.cards))
        skills = content.load_skills(Path(args.skills))
    except content.ContentError as exc:
        util.fail(str(exc))

    util.info(f"{len(cards)} quick card(s), {len(skills)} skill(s): format OK")
    for kind, items in (("quick card", cards), ("skill", skills)):
        drafts = [i["id"] for i in items if i["status"] == "draft"]
        if drafts:
            util.info(f"{kind} draft(s) waiting for review: {', '.join(drafts)}")

    if args.cards_json:
        left_out = content.write_cards_json(cards, Path(args.cards_json), include_drafts=args.allow_draft)
        util.info(f"wrote {args.cards_json}" + (f" (left out drafts: {', '.join(left_out)})" if left_out else ""))
    if args.skills_json:
        left_out = content.write_skills_json(skills, Path(args.skills_json), include_drafts=args.allow_draft)
        util.info(f"wrote {args.skills_json}" + (f" (left out drafts: {', '.join(left_out)})" if left_out else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
