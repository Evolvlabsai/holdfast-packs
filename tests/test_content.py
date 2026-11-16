"""The Markdown format for quick cards and survival skills (scripts/holdfast/content.py)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import check_content
from holdfast import content, util

CARDS = util.repo_root() / "packs" / "core" / "sources" / "cards"

CARD = """---
id: test-card
title: Test card
lead: One line under the title.
tone: normal
icon: heart
order: 999
source: A public source
status: draft
---

## First step

Do the first thing.
It can wrap over two lines.

## Second step

Do the second thing.

## Third step

Do the third thing.
"""

DRAWING = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 160" fill="none" stroke="#1C1F1A" stroke-width="3">
  <title>A jug</title>
  <path d="M80 40 h80 v100 h-80 z"/>
  <path class="accent" d="M120 20 v20"/>
</svg>
"""

SKILL = """---
id: test-skill
title: Test skill
summary: What it is for, in one line.
category: light
difficulty: easy
time: 5 minutes
order: 10
needs:
  - A jug of water
  - A headlamp
warnings:
  - Never leave a flame alone.
source: A public source
status: draft
---

## Fill the jug

![A jug full of water.](jug.svg)

Fill it.

## Add the light

Put the light on top.
"""


def _card(tmp_path: Path, text: str = CARD, name: str = "test-card.md") -> Path:
    folder = tmp_path / "cards"
    folder.mkdir(exist_ok=True)
    path = folder / name
    path.write_text(text, encoding="utf-8")
    return path


def _skill(tmp_path: Path, text: str = SKILL, drawing: str | None = DRAWING) -> Path:
    folder = tmp_path / "skills" / "test-skill"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "skill.md").write_text(text, encoding="utf-8")
    if drawing is not None:
        (folder / "jug.svg").write_text(drawing, encoding="utf-8")
    return folder


# --- the real cards ---------------------------------------------------------

def test_every_card_on_main_follows_the_format():
    cards = content.load_cards(CARDS)
    assert len(cards) >= 16
    assert [c["order"] for c in cards] == sorted(c["order"] for c in cards)


def test_the_first_card_is_still_the_red_bleeding_card():
    first = content.load_cards(CARDS)[0]
    assert (first["id"], first["tone"], first["timer"]) == ("bleeding", "danger", "tourniquet")


def test_the_export_is_what_the_app_reads(tmp_path):
    out = tmp_path / "cards.json"
    assert check_content.main(["--cards", str(CARDS), "--skills", str(tmp_path / "none"), "--cards-json", str(out)]) == 0
    cards = json.loads(out.read_text(encoding="utf-8"))
    assert set(cards[0]) == {"id", "title", "lead", "tone", "icon", "source", "timer", "draft", "steps"}
    assert all(c["draft"] is False for c in cards)


# --- cards: what a contributor can get wrong ---------------------------------

def test_a_good_card_parses_and_wrapped_lines_join(tmp_path):
    card = content.load_card(_card(tmp_path))
    assert card["draft"] is True and card["status"] == "draft"
    assert card["steps"][0] == {"title": "First step", "body": "Do the first thing. It can wrap over two lines."}


def test_a_draft_is_left_out_of_the_export(tmp_path):
    _card(tmp_path)
    out = tmp_path / "cards.json"
    left_out = content.write_cards_json(content.load_cards(tmp_path / "cards"), out)
    assert left_out == ["test-card"]
    assert json.loads(out.read_text(encoding="utf-8")) == []


@pytest.mark.parametrize(("change", "message"), [
    (("id: test-card", "id: other"), "make them match"),
    (("icon: heart", "icon: rocket"), "'icon' must be one of"),
    (("tone: normal", "tone: loud"), "'tone' must be one of"),
    (("order: 999", "order: first"), "whole number"),
    (("status: draft", "status: reviewed"), "reviewed: YYYY-MM-DD"),
    (("status: draft", "status: draft\nreviewed: 2026-11-16"), "a draft has no 'reviewed' date"),
    (("source: A public source\n", ""), "'source' is required"),
    (("lead: One line under the title.", "lead: " + "x" * 130), "keep it to 120"),
    (("Do the second thing.", "Give one 500 mg tablet."), "medicine dose"),
    (("## Third step\n\nDo the third thing.\n", ""), "3 to 8 steps"),
    (("Do the first thing.", "![A picture.](x.svg)\n\nDo the first thing."), "no pictures"),
    (("Do the second thing.", "Line one.\n\nA second paragraph."), "one paragraph"),
    (("## First step", "### First step"), "only '## ' headings"),
    (("title: Test card", "title: Test card\ncolor: red"), "unknown field"),
    (("---\nid", "id"), "must start with a '---' line"),
])
def test_a_broken_card_is_refused_with_a_reason(tmp_path, change, message):
    old, new = change
    assert old in CARD
    with pytest.raises(content.ContentError, match=message):
        content.load_card(_card(tmp_path, CARD.replace(old, new, 1)))


def test_two_cards_cannot_share_an_order(tmp_path):
    _card(tmp_path)
    _card(tmp_path, CARD.replace("id: test-card", "id: second-card"), "second-card.md")
    with pytest.raises(content.ContentError, match="share order"):
        content.load_cards(tmp_path / "cards")


# --- skills -------------------------------------------------------------------

def test_a_good_skill_parses(tmp_path):
    skill = content.load_skill(_skill(tmp_path))
    assert skill["needs"] == ["A jug of water", "A headlamp"]
    assert skill["steps"][0]["image"] == "jug.svg"
    assert skill["steps"][0]["alt"] == "A jug full of water."
    assert skill["steps"][1]["image"] is None


@pytest.mark.parametrize(("change", "message"), [
    (("warnings:\n  - Never leave a flame alone.\n", ""), "'warnings' needs at least one"),
    (("![A jug full of water.](jug.svg)", "![](jug.svg)"), "needs a description"),
    (("![A jug full of water.](jug.svg)", "![A jug.](../jug.svg)"), "own folder"),
    (("category: light", "category: weapons"), "'category' must be one of"),
    (("needs:\n  - A jug of water\n  - A headlamp\n", "needs:\n"), "'needs' needs at least one"),
])
def test_a_broken_skill_is_refused_with_a_reason(tmp_path, change, message):
    old, new = change
    assert old in SKILL
    with pytest.raises(content.ContentError, match=message):
        content.load_skill(_skill(tmp_path, SKILL.replace(old, new, 1)))


def test_a_water_skill_needs_no_warning(tmp_path):
    text = SKILL.replace("category: light", "category: water").replace("warnings:\n  - Never leave a flame alone.\n", "")
    assert content.load_skill(_skill(tmp_path, text))["warnings"] == []


def test_a_picture_no_step_uses_is_refused(tmp_path):
    folder = _skill(tmp_path)
    (folder / "spare.svg").write_text(DRAWING, encoding="utf-8")
    with pytest.raises(content.ContentError, match="files no step uses: spare.svg"):
        content.load_skill(folder)


# --- drawings ----------------------------------------------------------------

@pytest.mark.parametrize(("drawing", "message"), [
    (DRAWING.replace('viewBox="0 0 240 160"', 'viewBox="0 0 100 100"'), "viewBox must be"),
    (DRAWING.replace("<title>A jug</title>", "<script>alert(1)</script>"), "only <title> and <path>"),
    (DRAWING.replace("<title>A jug</title>", '<image href="https://example.com/x.png"/>'), "only <title> and <path>"),
    (DRAWING.replace('<path d=', '<path onclick="x()" d='), "'onclick' is not allowed"),
    (DRAWING.replace('class="accent"', 'class="glow"'), "path class must be"),
    (DRAWING.replace('d="M120 20 v20"', 'd="url(#x)"'), "plain path data"),
    ('<!DOCTYPE svg [<!ENTITY x "y">]>' + DRAWING, "not a valid, safe SVG"),
    ("not xml", "not a valid, safe SVG"),
])
def test_an_unsafe_or_odd_drawing_is_refused(tmp_path, drawing, message):
    with pytest.raises(content.ContentError, match=message):
        content.load_skill(_skill(tmp_path, drawing=drawing))


def test_a_missing_drawing_is_refused(tmp_path):
    with pytest.raises(content.ContentError, match="picture file is missing"):
        content.load_skill(_skill(tmp_path, drawing=None))


# --- skills in a built pack ----------------------------------------------------

def test_a_skill_lands_in_the_pack_with_its_drawing_inline(tmp_path):
    import shutil
    import sqlite3

    import build_core

    sources = tmp_path / "src"
    shutil.copytree(CARDS.parent / "cards", sources / "cards")
    skill_dir = _skill(tmp_path)
    shutil.copytree(skill_dir, sources / "skills" / "test-skill")
    out = tmp_path / "core.hfdb"

    with pytest.raises(SystemExit):
        build_core.main(["--sources", str(sources), "--out", str(out), "--id", "core"])  # a draft skill
    assert build_core.main(["--sources", str(sources), "--out", str(out), "--id", "core", "--allow-draft"]) == 0

    cn = sqlite3.connect(f"file:{out.as_posix()}?mode=ro", uri=True)
    try:
        skill_id, sort, raw = cn.execute("select skill_id, sort, json from skills").fetchone()
    finally:
        cn.close()
    skill = json.loads(raw)
    assert (skill_id, sort) == ("test-skill", 0)
    assert "folder" not in skill and "status" not in skill
    drawing = skill["steps"][0]["drawing"]
    assert drawing["alt"] == "A jug full of water."
    assert drawing["paths"] == [{"d": "M80 40 h80 v100 h-80 z", "style": "line"},
                                {"d": "M120 20 v20", "style": "accent"}]
    assert skill["steps"][1]["drawing"] is None


def test_a_pack_without_skills_has_no_skills_table(tmp_path):
    import shutil
    import sqlite3

    import build_core

    sources = tmp_path / "src"
    shutil.copytree(CARDS, sources / "cards")
    out = tmp_path / "core.hfdb"
    assert build_core.main(["--sources", str(sources), "--out", str(out), "--id", "core"]) == 0
    cn = sqlite3.connect(f"file:{out.as_posix()}?mode=ro", uri=True)
    try:
        tables = {r[0] for r in cn.execute("select name from sqlite_master where type = 'table'")}
    finally:
        cn.close()
    assert "skills" not in tables


def test_a_drawing_with_an_arc_is_refused(tmp_path):
    drawing = DRAWING.replace('d="M120 20 v20"', 'd="M100 20 A10 10 0 0 1 120 20"')
    with pytest.raises(content.ContentError, match="no arcs"):
        content.load_skill(_skill(tmp_path, drawing=drawing))
