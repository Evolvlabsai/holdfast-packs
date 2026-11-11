"""build_core.py on the repo's real sources must produce a pack the app accepts.

This is the end-to-end check: the reviewed content in ``packs/core/sources`` goes
in, a ``core.hfdb`` comes out, and it answers the app's own search SQL.
"""

from __future__ import annotations

import json
import shutil

import pytest

import build_core
from holdfast import hfdb, util

SOURCES = util.repo_root() / "packs" / "core" / "sources"


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("dist") / "core.hfdb"
    code = build_core.main(
        [
            "--sources", str(SOURCES),
            "--out", str(out),
            "--id", "core",
            "--name", "Core",
            "--version", "2026.11.09",
            "--region", "US-MD",
        ]
    )
    assert code == 0
    return out


def test_sources_are_present():
    assert (SOURCES / "cards.json").exists()
    assert list((SOURCES / "docs").glob("*.md"))


def test_no_invented_map_points_ship():
    """The old SAMPLE overlay points were made up. Core ships no overlays until a real source exists."""
    assert not list((SOURCES / "overlays").glob("*.geojson"))


def test_the_pack_has_cards_and_docs_and_no_overlays(built):
    described = hfdb.describe(built)
    assert described["meta"]["id"] == "core"
    assert described["meta"]["version"] == "2026.11.09"
    assert described["meta"]["region"] == "US-MD"
    assert described["docs"] == len(list((SOURCES / "docs").glob("*.md")))
    assert described["cards"] > 0
    assert described["overlays"] == 0


def test_searching_it_finds_the_water_guidance(built):
    hits = hfdb.search(built, "boil water")
    assert hits
    assert any("water" in hit["title"].lower() for hit in hits)


def test_every_hit_carries_a_location_the_app_can_cite(built):
    for hit in hfdb.search(built, "water"):
        assert hit["location"].endswith(".md")


def test_titles_come_from_the_markdown_heading(built):
    assert any(h["title"] == "Build an emergency kit" for h in hfdb.search(built, "emergency kit"))


def test_the_source_line_is_stored_and_kept_out_of_the_body(built):
    import sqlite3

    cn = sqlite3.connect(f"file:{built.as_posix()}?mode=ro", uri=True)
    try:
        body, source = cn.execute("select body, source from docs where doc_id = 'build-a-kit'").fetchone()
    finally:
        cn.close()
    assert source and "Ready.gov" in source
    assert not body.lower().startswith("source:")
    assert "Source:" not in body.splitlines()[0]


def test_cards_are_stored_in_home_grid_order(built):
    import sqlite3

    source_ids = [c["id"] for c in json.loads((SOURCES / "cards.json").read_text(encoding="utf-8"))]
    cn = sqlite3.connect(f"file:{built.as_posix()}?mode=ro", uri=True)
    try:
        rows = cn.execute("select card_id, sort from cards order by sort").fetchall()
    finally:
        cn.close()
    assert [r[0] for r in rows] == source_ids
    assert [r[1] for r in rows] == list(range(len(source_ids)))


def test_an_overlay_keeps_its_geojson_verbatim(tmp_path):
    import sqlite3

    raw = json.dumps({
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-76.5, 39.0]},
            "properties": {"kind": "water", "name": "Test point"},
        }],
    })
    sources = tmp_path / "src"
    shutil.copytree(SOURCES, sources)
    (sources / "overlays").mkdir(exist_ok=True)
    (sources / "overlays" / "us-md-test.geojson").write_text(raw, encoding="utf-8")
    out = tmp_path / "core.hfdb"
    assert build_core.main(["--sources", str(sources), "--out", str(out), "--id", "core"]) == 0

    cn = sqlite3.connect(f"file:{out.as_posix()}?mode=ro", uri=True)
    try:
        overlay_id, region, geojson = cn.execute("select overlay_id, region, geojson from overlays").fetchone()
    finally:
        cn.close()
    assert overlay_id == "us-md-test"
    assert region == "US-MD"
    assert json.loads(geojson) == json.loads(raw)


def test_every_source_card_is_reviewed():
    """The quick cards passed medical review on 2026-11-11; none may go back to draft unnoticed."""
    cards = json.loads((SOURCES / "cards.json").read_text(encoding="utf-8"))
    assert cards
    assert [c["id"] for c in cards if c.get("draft")] == []


def test_building_a_draft_card_without_allow_draft_is_refused(tmp_path):
    """An unreviewed card must never reach a release by accident."""
    sources = tmp_path / "src"
    shutil.copytree(SOURCES, sources)
    cards = json.loads((sources / "cards.json").read_text(encoding="utf-8"))
    cards[0]["draft"] = True
    (sources / "cards.json").write_text(json.dumps(cards), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        build_core.main(["--sources", str(sources), "--out", str(tmp_path / "core.hfdb"), "--id", "core"])
    assert exc.value.code == 1


def test_region_is_guessed_from_an_overlay_file_name():
    assert build_core.region_from_id("us-md-sample") == "US-MD"
    assert build_core.region_from_id("us-va-shelters") == "US-VA"
    assert build_core.region_from_id("shelters") == ""


def test_an_empty_sources_directory_is_refused(tmp_path):
    (tmp_path / "empty").mkdir()
    with pytest.raises(SystemExit):
        build_core.main(["--sources", str(tmp_path / "empty"), "--out", str(tmp_path / "x.hfdb")])


def test_duplicate_doc_ids_are_refused(tmp_path):
    sources = tmp_path / "src"
    (sources / "docs" / "a").mkdir(parents=True)
    (sources / "docs" / "b").mkdir(parents=True)
    (sources / "docs" / "a" / "same.md").write_text("# One\n\nbody one\n", encoding="utf-8")
    (sources / "docs" / "b" / "same.md").write_text("# Two\n\nbody two\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        build_core.main(["--sources", str(sources), "--out", str(tmp_path / "x.hfdb")])


def test_the_verification_query_flag_fails_a_pack_that_cannot_answer(tmp_path):
    sources = tmp_path / "src"
    (sources / "docs").mkdir(parents=True)
    (sources / "docs" / "one.md").write_text("# One\n\nnothing about water here\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        build_core.main(
            ["--sources", str(sources), "--out", str(tmp_path / "x.hfdb"), "--query", "zzzznotpresent"]
        )
