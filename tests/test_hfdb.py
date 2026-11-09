"""The hfdb writer must produce a file the app can actually read and search.

These tests do two separate jobs:

1. assert the schema SQL is still byte-identical to the app's ``HfdbSchema.CreateSql``
   (the string is duplicated on purpose -- if the app changes it, this test fails
   and someone has to look, instead of packs quietly going unreadable); and
2. query a built pack with the app's own SQL, including the FTS5 ``MATCH``
   expression ``LibrarySearch.BuildMatchExpression`` builds from user input.
"""

from __future__ import annotations

import json
import sqlite3

import pytest

from holdfast import hfdb

# Verbatim from src/Holdfast.Core/Search/LibrarySearch.cs, HfdbSchema.CreateSql
# in the private holdfast-app repo. Keep the two in sync by hand; that is the
# point of this test.
APP_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS docs (
    doc_id   TEXT PRIMARY KEY,
    title    TEXT,
    body     TEXT,
    location TEXT,
    source   TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
    title,
    body,
    content='docs',
    content_rowid='rowid',
    tokenize='porter unicode61'
);

CREATE TABLE IF NOT EXISTS cards (
    card_id TEXT PRIMARY KEY,
    sort    INTEGER,
    json    TEXT
);

CREATE TABLE IF NOT EXISTS overlays (
    overlay_id TEXT PRIMARY KEY,
    region     TEXT,
    geojson    TEXT
);
"""

APP_REBUILD_SQL = "INSERT INTO docs_fts(docs_fts) VALUES('rebuild');"

GEOJSON = json.dumps(
    {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-76.4922, 38.9784]},
                "properties": {"kind": "rally", "name": "TEST rally point"},
            }
        ],
    }
)


def build(path, **kwargs):
    with hfdb.HfdbWriter(path, kwargs.get("pack_id", "test"), "Test pack", "2026.11.09") as w:
        w.add_document(
            "tourniquet",
            "Stop bleeding",
            "Apply a tourniquet 2-3 inches above the wound, not on a joint. Note the time it went on.",
            "docs/bleeding.md",
            "Stop the Bleed guidance",
        )
        w.add_document(
            "boil-water",
            "Make water safe by boiling",
            "Bring water to a rolling boil for one minute. Above 6,500 feet, boil for three minutes.",
            "docs/boiling.md",
            "CDC",
        )
        w.add_document("page", "ATP 3-50.21 — p. 14", "Improvised shelter construction in cold weather.", "p. 14", None)
        w.add_card({"id": "bleeding", "title": "Stop bleeding", "steps": []}, 0)
        w.add_overlay("us-md-test", "US-MD", GEOJSON)
        return w.complete()


# -- schema ----------------------------------------------------------------


def test_create_sql_matches_the_app_exactly():
    assert hfdb.CREATE_SQL.strip() == APP_CREATE_SQL.strip()
    assert hfdb.REBUILD_FTS_SQL == APP_REBUILD_SQL


def test_built_file_has_the_app_tables(tmp_path):
    path = build(tmp_path / "pack.hfdb")
    cn = sqlite3.connect(path)
    try:
        names = {r[0] for r in cn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
    finally:
        cn.close()
    assert {"meta", "docs", "docs_fts", "cards", "overlays"} <= names

    sql = next(
        r[0]
        for r in sqlite3.connect(path).execute("SELECT sql FROM sqlite_master WHERE name = 'docs_fts'")
    )
    assert "content='docs'" in sql
    assert "tokenize='porter unicode61'" in sql


def test_meta_carries_id_name_version(tmp_path):
    path = build(tmp_path / "pack.hfdb", pack_id="core")
    described = hfdb.describe(path)
    assert described["meta"]["id"] == "core"
    assert described["meta"]["name"] == "Test pack"
    assert described["meta"]["version"] == "2026.11.09"
    assert described["docs"] == 3
    assert described["cards"] == 1
    assert described["overlays"] == 1


# -- search ----------------------------------------------------------------


def test_fts5_match_finds_a_document(tmp_path):
    """The headline check: a plain FTS5 MATCH query against the built index."""
    path = build(tmp_path / "pack.hfdb")
    cn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        rows = cn.execute(
            "select d.doc_id, d.title from docs_fts join docs d on d.rowid = docs_fts.rowid "
            "where docs_fts match ?",
            ("tourniquet",),
        ).fetchall()
    finally:
        cn.close()
    assert [r[0] for r in rows] == ["tourniquet"]


def test_search_uses_the_apps_own_sql_and_ranking(tmp_path):
    path = build(tmp_path / "pack.hfdb")
    hits = hfdb.search(path, "boil water")
    assert [h["doc_id"] for h in hits] == ["boil-water"]
    hit = hits[0]
    assert hit["location"] == "docs/boiling.md"
    assert "boil" in hit["snippet"].lower()
    # bm25 is negative and lower-is-better; the app flips it, so a hit scores > 0.
    assert hit["score"] > 0


def test_title_matches_outrank_body_matches(tmp_path):
    """The app weighs the title column 10x (bm25(docs_fts, 10.0, 1.0))."""
    path = tmp_path / "rank.hfdb"
    with hfdb.HfdbWriter(path, "rank", "Rank", "2026.11.09") as w:
        w.add_document("in-title", "Hypothermia", "Unrelated body text about keeping dry.")
        w.add_document("in-body", "Cold weather", "Watch for hypothermia: shivering, confusion, slurred speech.")
        w.complete()

    hits = hfdb.search(path, "hypothermia")
    assert [h["doc_id"] for h in hits] == ["in-title", "in-body"]


def test_prefix_search_matches_a_partial_word(tmp_path):
    path = build(tmp_path / "pack.hfdb")
    assert [h["doc_id"] for h in hfdb.search(path, "tourni")] == ["tourniquet"]


def test_porter_stemming_is_active(tmp_path):
    """tokenize='porter' is why a search for 'boiling' finds 'boil'."""
    path = build(tmp_path / "pack.hfdb")
    assert [h["doc_id"] for h in hfdb.search(path, "boiled")] == ["boil-water"]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("tourniquet", '"tourniquet"*'),
        ("boil water", '"boil"* AND "water"*'),
        ('a "b" -c*', '"a"* AND "b"* AND "c"*'),
        ("   ", None),
        ("", None),
        ("!!!", None),
    ],
)
def test_match_expression_matches_the_app(query, expected):
    assert hfdb.build_match_expression(query) == expected


def test_match_expression_caps_at_sixteen_terms():
    expression = hfdb.build_match_expression(" ".join(f"w{i}" for i in range(40)))
    assert expression is not None
    assert expression.count(" AND ") == 15


def test_fts5_syntax_in_user_input_cannot_break_the_query(tmp_path):
    """A user typing FTS5 operators must get no results, not a SQL error."""
    path = build(tmp_path / "pack.hfdb")
    assert hfdb.search(path, 'water OR NEAR("x" "y")') == []
    assert hfdb.search(path, "***") == []


# -- integrity and refusals ------------------------------------------------


def test_index_survives_the_vacuum(tmp_path):
    """complete() VACUUMs; docs has a TEXT primary key, so rowids could move."""
    path = build(tmp_path / "pack.hfdb")
    cn = sqlite3.connect(path)
    try:
        cn.execute("INSERT INTO docs_fts(docs_fts) VALUES('integrity-check')")
    finally:
        cn.close()


def test_card_without_an_id_is_refused(tmp_path):
    with pytest.raises(hfdb.HfdbError, match="no string 'id'"):
        with hfdb.HfdbWriter(tmp_path / "bad.hfdb", "bad", "Bad", "2026.11.09") as w:
            w.add_card({"title": "no id here"}, 0)


def test_overlay_with_an_unknown_kind_is_refused(tmp_path):
    bad = json.dumps(
        {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [0, 0]},
                    "properties": {"kind": "pharmacy", "name": "x"},
                }
            ],
        }
    )
    with pytest.raises(hfdb.HfdbError, match="properties.kind"):
        with hfdb.HfdbWriter(tmp_path / "bad.hfdb", "bad", "Bad", "2026.11.09") as w:
            w.add_overlay("x", "US-MD", bad)


def test_overlay_that_is_not_a_feature_collection_is_refused(tmp_path):
    with pytest.raises(hfdb.HfdbError, match="FeatureCollection"):
        with hfdb.HfdbWriter(tmp_path / "bad.hfdb", "bad", "Bad", "2026.11.09") as w:
            w.add_overlay("x", "US-MD", json.dumps({"type": "Feature"}))


def test_a_failed_build_leaves_no_file_behind(tmp_path):
    path = tmp_path / "half.hfdb"
    with pytest.raises(RuntimeError):
        with hfdb.HfdbWriter(path, "half", "Half", "2026.11.09") as w:
            w.add_document("one", "One", "body")
            raise RuntimeError("build blew up")
    assert not path.exists()


def test_rebuilding_a_pack_overwrites_the_old_file(tmp_path):
    path = tmp_path / "pack.hfdb"
    build(path)
    first = path.stat().st_size
    with hfdb.HfdbWriter(path, "test", "Test pack", "2026.11.10") as w:
        w.add_document("only", "Only doc", "short body about water")
        w.complete()
    assert hfdb.describe(path)["docs"] == 1
    assert path.stat().st_size <= first
