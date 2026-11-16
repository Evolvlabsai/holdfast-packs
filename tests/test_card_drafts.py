"""New quick cards wait in packs/core/review/ until they pass medical review.

They move into sources/cards.json (with "draft": false) only after review, so the
weekly build never ships one by accident.
"""

from __future__ import annotations

import json

from holdfast import util

CORE = util.repo_root() / "packs" / "core"
DRAFTS = CORE / "review" / "cards-draft.json"
DOSE_WORDS = ("mg", "milligram", "ml of", "tablet", "capsule", "dose of")
# Glyphs the app draws (src/Holdfast.App/Controls/Icons.cs). Unknown ones show an info icon.
APP_ICONS = {"drop", "heart", "water", "cold", "signal", "shelter", "alert", "shield-alert", "timer",
             "plus", "bolt", "pill", "compass", "flame", "sun", "info", "other"}


def _drafts() -> list[dict]:
    if not DRAFTS.exists():
        return []
    return json.loads(DRAFTS.read_text(encoding="utf-8"))


def test_drafts_are_marked_draft_and_complete():
    for card in _drafts():
        assert card["draft"] is True, card["id"]
        assert card["title"] and card["lead"] and card["source"], card["id"]
        assert 3 <= len(card["steps"]) <= 6, card["id"]
        assert all(s["title"] and s["body"] for s in card["steps"]), card["id"]
        assert card["icon"] in APP_ICONS, card["id"]


def test_draft_ids_are_new():
    published = {c["id"] for c in json.loads((CORE / "sources" / "cards.json").read_text(encoding="utf-8"))}
    ids = [c["id"] for c in _drafts()]
    assert len(ids) == len(set(ids))
    assert not set(ids) & published


def test_drafts_carry_no_medicine_doses():
    for card in _drafts():
        for step in card["steps"]:
            body = step["body"].lower()
            assert not any(word in body for word in DOSE_WORDS), (card["id"], step["title"])
