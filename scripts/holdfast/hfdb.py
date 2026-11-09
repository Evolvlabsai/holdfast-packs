"""Writer for the ``hfdb`` content-pack format (one SQLite file per pack).

The schema below must stay byte-identical to ``HfdbSchema.CreateSql`` in the app
(``src/Holdfast.Core/Search/LibrarySearch.cs``, private ``holdfast-app`` repo).
The app opens every pack read-only and skips any pack it cannot read, so a pack
built with a drifted schema fails silently on the phone: that is why
``tests/test_hfdb.py`` asserts the SQL text and queries the result the same way
``LibrarySearch`` does.

Tables (see the app's doc comment):

* ``meta(key TEXT PRIMARY KEY, value TEXT)`` -- keys: ``id``, ``name``, ``version``.
* ``docs(doc_id TEXT PRIMARY KEY, title, body, location, source)``.
* ``docs_fts`` -- FTS5 over ``(title, body)``, ``content='docs'``,
  ``tokenize='porter unicode61'``. External content: the index is built with
  ``INSERT INTO docs_fts(docs_fts) VALUES('rebuild')`` after the rows land.
* ``cards(card_id TEXT PRIMARY KEY, sort INTEGER, json TEXT)`` -- one quick card
  as JSON per row, in Home-grid order.
* ``overlays(overlay_id TEXT PRIMARY KEY, region TEXT, geojson TEXT)`` -- a
  GeoJSON FeatureCollection whose features carry ``properties.kind`` in
  {rally, water, medical, shelter, fuel} and ``properties.name``.

Content packs are plain, unencrypted SQLite; only the on-device vault is encrypted.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from types import TracebackType

# Copied verbatim from Holdfast.Core.Search.HfdbSchema.CreateSql.
CREATE_SQL = """
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

REBUILD_FTS_SQL = "INSERT INTO docs_fts(docs_fts) VALUES('rebuild');"

#: The overlay feature kinds the app's map layer toggles understand.
OVERLAY_KINDS = ("rally", "water", "medical", "shelter", "fuel")


class HfdbError(RuntimeError):
    """A pack could not be written, or was written wrong."""


def require_fts5() -> None:
    """Fail early and clearly when the interpreter's SQLite has no FTS5."""
    cn = sqlite3.connect(":memory:")
    try:
        cn.execute("CREATE VIRTUAL TABLE fts5_probe USING fts5(a)")
    except sqlite3.OperationalError as exc:  # pragma: no cover - environment dependent
        raise HfdbError(
            "this Python's SQLite was built without FTS5; hfdb packs cannot be built "
            f"({exc}). Use the python.org 3.12 build or a distro package with FTS5."
        ) from exc
    finally:
        cn.close()


class HfdbWriter:
    """Builds one ``hfdb`` file. Overwrites ``path`` if it exists.

    Use as a context manager; ``complete()`` rebuilds the FTS index, verifies it
    and closes the file. Leaving the block without ``complete()`` (an exception,
    say) rolls back and deletes the half-written file, so a failed build never
    leaves something a release job could upload.
    """

    def __init__(self, path: str | Path, pack_id: str, name: str, version: str) -> None:
        if not pack_id:
            raise ValueError("pack_id is required")
        require_fts5()

        self.path = Path(path).resolve()
        self.pack_id = pack_id
        self.docs = 0
        self.cards = 0
        self.overlays = 0
        self._completed = False
        self._closed = False

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.unlink(missing_ok=True)

        self._cn = sqlite3.connect(self.path, isolation_level=None)
        self._cn.execute("PRAGMA journal_mode = DELETE")
        self._cn.executescript(CREATE_SQL)
        self._cn.execute("BEGIN")

        self._set_meta("id", pack_id)
        self._set_meta("name", name or pack_id)
        self._set_meta("version", version or "")

    # -- context manager ---------------------------------------------------

    def __enter__(self) -> "HfdbWriter":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._completed:
            return
        self.abort()

    # -- writing -----------------------------------------------------------

    def set_meta(self, key: str, value: str) -> None:
        """Set an extra ``meta`` key. The app reads only id/name/version today;
        anything else is informational (``region``, ``built``, ``generator``)."""
        self._set_meta(key, value)

    def add_document(
        self,
        doc_id: str,
        title: str,
        body: str,
        location: str = "",
        source: str | None = None,
    ) -> None:
        """Add or replace one searchable document.

        ``location`` is what the app shows and cites next to a hit: a relative
        path for markdown docs, ``"p. 14"`` for a page of a PDF.
        """
        if not doc_id:
            raise ValueError("doc_id is required")
        self._cn.execute(
            """
            INSERT INTO docs (doc_id, title, body, location, source) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(doc_id) DO UPDATE SET title = excluded.title, body = excluded.body,
                location = excluded.location, source = excluded.source
            """,
            (doc_id, title or "", body or "", location or "", source),
        )
        self.docs += 1

    def add_card(self, card: dict, sort: int) -> None:
        """Add one quick card from its parsed JSON object (must carry ``id``)."""
        card_id = card.get("id")
        if not isinstance(card_id, str) or not card_id:
            raise HfdbError(f"quick card at sort {sort} has no string 'id'")
        self.add_card_json(card_id, sort, json.dumps(card, ensure_ascii=False, indent=2))

    def add_card_json(self, card_id: str, sort: int, raw_json: str) -> None:
        if not card_id:
            raise ValueError("card_id is required")
        self._cn.execute(
            """
            INSERT INTO cards (card_id, sort, json) VALUES (?, ?, ?)
            ON CONFLICT(card_id) DO UPDATE SET sort = excluded.sort, json = excluded.json
            """,
            (card_id, int(sort), raw_json or ""),
        )
        self.cards += 1

    def add_overlay(self, overlay_id: str, region: str, geojson_text: str) -> None:
        """Add one GeoJSON FeatureCollection. The text is validated, not rewritten."""
        if not overlay_id:
            raise ValueError("overlay_id is required")
        try:
            parsed = json.loads(geojson_text)
        except json.JSONDecodeError as exc:
            raise HfdbError(f"overlay '{overlay_id}' is not valid JSON: {exc}") from exc
        if not isinstance(parsed, dict) or parsed.get("type") != "FeatureCollection":
            raise HfdbError(f"overlay '{overlay_id}' must be a GeoJSON FeatureCollection")

        for i, feature in enumerate(parsed.get("features") or []):
            props = (feature or {}).get("properties") or {}
            kind = props.get("kind")
            if kind not in OVERLAY_KINDS:
                raise HfdbError(
                    f"overlay '{overlay_id}' feature {i}: properties.kind is {kind!r}, "
                    f"expected one of {', '.join(OVERLAY_KINDS)}"
                )
            if not props.get("name"):
                raise HfdbError(f"overlay '{overlay_id}' feature {i}: properties.name is missing")

        self._cn.execute(
            """
            INSERT INTO overlays (overlay_id, region, geojson) VALUES (?, ?, ?)
            ON CONFLICT(overlay_id) DO UPDATE SET region = excluded.region, geojson = excluded.geojson
            """,
            (overlay_id, region or "", geojson_text),
        )
        self.overlays += 1

    # -- finishing ---------------------------------------------------------

    def complete(self) -> Path:
        """Commit, build the FTS index, verify it, compact and close."""
        if self._completed:
            return self.path

        self._cn.execute("COMMIT")
        self._cn.execute(REBUILD_FTS_SQL)

        # Same two statements the app's HfdbWriter.Complete runs. PRAGMA optimize
        # may add SQLite's own sqlite_stat1 statistics table, which is the one
        # object a pack built here can have that a PackTool-built pack does not.
        # It is internal to SQLite, helps the query planner, and the app opens
        # packs read-only, so it changes nothing the app sees.
        self._cn.execute("PRAGMA optimize")

        # VACUUM may renumber the rowids of a table without an INTEGER PRIMARY KEY,
        # which is exactly what docs_fts maps against, so the index is verified after
        # it and not before. integrity-check reads every row through the index.
        self._cn.execute("VACUUM")
        try:
            self._cn.execute("INSERT INTO docs_fts(docs_fts) VALUES('integrity-check')")
        except sqlite3.DatabaseError as exc:
            self._cn.execute(REBUILD_FTS_SQL)
            self._cn.execute("INSERT INTO docs_fts(docs_fts) VALUES('integrity-check')")
            print(f"note: FTS index rebuilt after VACUUM renumbered rowids ({exc})")

        self._completed = True
        self._close()
        return self.path

    def abort(self) -> None:
        """Roll back and delete the half-written file."""
        if self._closed:
            return
        try:
            self._cn.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        self._close()
        self.path.unlink(missing_ok=True)

    def _close(self) -> None:
        if not self._closed:
            self._closed = True
            self._cn.close()

    def _set_meta(self, key: str, value: str) -> None:
        self._cn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def describe(path: str | Path) -> dict:
    """Read a built pack back the way the app does. Used by builds and tests."""
    cn = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
    try:
        meta = dict(cn.execute("SELECT key, value FROM meta").fetchall())
        return {
            "meta": meta,
            "docs": cn.execute("SELECT count(*) FROM docs").fetchone()[0],
            "cards": cn.execute("SELECT count(*) FROM cards").fetchone()[0],
            "overlays": cn.execute("SELECT count(*) FROM overlays").fetchone()[0],
            "bytes": Path(path).stat().st_size,
        }
    finally:
        cn.close()


def build_match_expression(query: str) -> str | None:
    """The same FTS5 MATCH expression the app builds from user input.

    Mirrors ``LibrarySearch.BuildMatchExpression``: split on non-alphanumerics,
    quote each word, make it a prefix term, AND them, cap at 16 terms. Kept here
    so the pipeline can prove a built pack answers the app's real queries.
    """
    terms: list[str] = []
    word: list[str] = []

    def flush() -> None:
        if word and len(terms) < 16:
            terms.append('"' + "".join(word).replace('"', '""') + '"*')
        word.clear()

    for ch in query or "":
        if ch.isalnum():
            word.append(ch)
        else:
            flush()
    flush()
    return " AND ".join(terms) if terms else None


def search(path: str | Path, query: str, limit: int = 40) -> list[dict]:
    """Run the app's own search SQL against a built pack (verification aid)."""
    match = build_match_expression(query)
    if match is None:
        return []
    rank = "bm25(docs_fts, 10.0, 1.0)"
    cn = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
    try:
        rows = cn.execute(
            f"""
            select d.doc_id, d.title, snippet(docs_fts, 1, '', '', '…', 14), d.location, {rank}
            from docs_fts
            join docs d on d.rowid = docs_fts.rowid
            where docs_fts match ?
            order by {rank}
            limit ?
            """,
            (match, limit),
        ).fetchall()
    finally:
        cn.close()
    return [
        {
            "doc_id": r[0],
            "title": r[1],
            "snippet": " ".join((r[2] or "").split()),
            "location": r[3],
            "score": -r[4],
        }
        for r in rows
    ]
