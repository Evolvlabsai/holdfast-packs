"""The "News & tips" feed: ``news/items/*.json`` + ``news/img/*`` -> ``news.json``.

``news.json`` is signed exactly like ``manifest.json`` (same key, same detached
``.sig`` format, over the file's exact bytes), so it has one canonical writer:
:func:`write`, which goes through :func:`holdfast.util.write_json` (two-space
indent, UTF-8, LF, one trailing newline). Nothing here depends on the clock or
the machine, so building twice from the same sources gives identical bytes.

What the app reads (the contract): see ``schema/news.schema.json``. What a
schema cannot express is checked here:

* ids unique, and each source file named ``<id>.json``;
* dates that are real calendar dates, ``expires`` not before ``date``;
* lengths in UTF-16 code units too (the app is .NET; JSON Schema counts code
  points, so an emoji would otherwise slip one char past a C# length check);
* body formatting: paragraphs split by one blank line, ``"- "`` bullet lines,
  and nothing that looks like Markdown or HTML;
* images: JPEG/PNG/WebP whose real format matches the extension, at most
  :data:`MAX_IMAGE_BYTES` bytes and :data:`MAX_IMAGE_SIDE` px on the longest
  side, with sha256/size/width/height computed here, never typed by hand.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import util

SCHEMA = 1
MAX_ITEMS = 50
MAX_TITLE = 80
MAX_SUMMARY = 200
MAX_BODY = 4000
MAX_ALT = 200

#: 400 KB, read strictly as 400,000 bytes so no reading of "KB" lets an image
#: past a stricter check in the app.
MAX_IMAGE_BYTES = 400_000
MAX_IMAGE_SIDE = 1600

#: Pillow format name for each allowed extension.
IMAGE_FORMATS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}

#: Where the Pages site serves ``news/img/``.
BASE_URL = "https://evolvlabsai.github.io/holdfast-packs/"
IMAGE_URL_PREFIX = BASE_URL + "news/img/"

ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FILE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*\.(jpg|jpeg|png|webp)$")

#: Field order in the published item. Fixed so the bytes never depend on how a
#: source file happened to be written.
ITEM_ORDER = ("id", "date", "kind", "title", "summary", "body", "image", "expires", "minAppVersion")
KIND_ORDER = {"news": 0, "tip": 1}

#: Body lines the app would render literally and wrongly.
_MARKUP = (
    (re.compile(r"^#"), "a Markdown heading ('#')"),
    (re.compile(r"^[*+] "), "a '*' or '+' bullet (use '- ')"),
    (re.compile(r"^-(?! )"), "a '-' not followed by one space"),
    (re.compile(r"^- \s"), "a bullet with more than one space after '-'"),
    (re.compile(r"^\d+[.)] "), "a numbered list (use '- ' bullets)"),
    (re.compile(r"^>"), "a Markdown quote ('>')"),
    (re.compile(r"\*\*|__|`"), "Markdown emphasis or code"),
    (re.compile(r"\]\("), "a Markdown link ('](')"),
    (re.compile(r"<[A-Za-z/!]"), "something that looks like an HTML tag"),
)


class NewsError(ValueError):
    """One or more items are not publishable. ``problems`` lists every one."""

    def __init__(self, problems: list[str]):
        super().__init__("\n".join(problems))
        self.problems = problems


# -- paths ------------------------------------------------------------------


def news_dir(root: Path | None = None) -> Path:
    return (root or util.repo_root()) / "news"


def items_dir(root: Path | None = None) -> Path:
    return news_dir(root) / "items"


def img_dir(root: Path | None = None) -> Path:
    return news_dir(root) / "img"


def news_path(root: Path | None = None) -> Path:
    return (root or util.repo_root()) / "news.json"


def schema_path() -> Path:
    """Always the repo's schema, even when building a tree somewhere else."""
    return util.repo_root() / "schema" / "news.schema.json"


# -- schema -----------------------------------------------------------------


def _schema() -> dict:
    return json.loads(schema_path().read_text(encoding="utf-8"))


def _validator(ref: str | None = None):
    import jsonschema

    schema = _schema()
    if ref:
        schema = {"$schema": schema["$schema"], "$defs": schema["$defs"], "$ref": f"#/$defs/{ref}"}
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def _schema_errors(validator, document: Any, where: str) -> list[str]:
    out = []
    for err in sorted(validator.iter_errors(document), key=lambda e: list(e.absolute_path)):
        path = "/".join(str(p) for p in err.absolute_path) or "(root)"
        out.append(f"{where}: {path}: {err.message}")
    return out


# -- checks the schema cannot make -------------------------------------------


def utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def parse_date(value: Any) -> _dt.date | None:
    if not isinstance(value, str) or not DATE_RE.match(value):
        return None
    try:
        return _dt.date.fromisoformat(value)
    except ValueError:
        return None


def body_problems(body: str) -> list[str]:
    """Why ``body`` is not plain paragraphs and ``- `` bullets. Empty means fine."""
    problems: list[str] = []
    if body != body.strip():
        problems.append("starts or ends with whitespace")
    if "\r" in body or "\t" in body:
        problems.append("contains a carriage return or tab")
    if "\n\n\n" in body:
        problems.append("has more than one blank line in a row")
    for number, line in enumerate(body.split("\n"), start=1):
        if line == "":
            continue
        if line != line.strip():
            problems.append(f"line {number} has leading or trailing whitespace")
        for pattern, what in _MARKUP:
            if pattern.search(line):
                problems.append(f"line {number} has {what}: {line[:40]!r}")
                break
    return problems


def _length_problems(item: dict, where: str) -> list[str]:
    problems = []
    limits = {"title": MAX_TITLE, "summary": MAX_SUMMARY, "body": MAX_BODY}
    for name, limit in limits.items():
        value = item.get(name)
        if isinstance(value, str) and utf16_len(value) > limit:
            problems.append(f"{where}: {name} is {utf16_len(value)} UTF-16 units; the limit is {limit}")
    image = item.get("image")
    if isinstance(image, dict) and isinstance(image.get("alt"), str) and utf16_len(image["alt"]) > MAX_ALT:
        problems.append(f"{where}: image alt is longer than {MAX_ALT}")
    return problems


@dataclass
class ImageInfo:
    file: str
    size: int
    sha256: str
    width: int
    height: int

    def published(self, alt: str) -> dict:
        return {
            "url": IMAGE_URL_PREFIX + self.file,
            "sha256": self.sha256,
            "size": self.size,
            "width": self.width,
            "height": self.height,
            "alt": alt,
        }


def inspect_image(path: Path) -> tuple[ImageInfo | None, list[str]]:
    """Measure one image and check it against the feed's limits."""
    from PIL import Image, UnidentifiedImageError

    where = f"news/img/{path.name}"
    problems: list[str] = []
    if not FILE_RE.match(path.name):
        return None, [f"{where}: file name must be lower-case [a-z0-9._-] with .jpg, .jpeg, .png or .webp"]
    if not path.is_file():
        return None, [f"{where}: not found"]
    size, sha = util.size_and_sha256(path)
    if size > MAX_IMAGE_BYTES:
        problems.append(f"{where}: {size} bytes; the limit is {MAX_IMAGE_BYTES}")
    try:
        with Image.open(path) as im:
            fmt, (width, height) = im.format, im.size
            im.verify()
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        return None, problems + [f"{where}: not a readable image ({exc})"]
    expected = IMAGE_FORMATS[path.suffix.lower()]
    if fmt != expected:
        problems.append(f"{where}: the extension says {expected} but the file is {fmt}")
    if max(width, height) > MAX_IMAGE_SIDE:
        problems.append(f"{where}: {width}x{height}; the longest side may be at most {MAX_IMAGE_SIDE} px")
    if problems:
        return None, problems
    return ImageInfo(path.name, size, sha, width, height), []


# -- building ---------------------------------------------------------------


@dataclass
class BuildResult:
    feed: dict
    dropped: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def load_sources(root: Path | None = None) -> list[tuple[Path, Any]]:
    folder = items_dir(root)
    if not folder.is_dir():
        raise NewsError([f"{folder}: no news/items folder"])
    out = []
    problems = []
    for path in sorted(folder.iterdir()):
        if path.is_dir() or path.name.startswith("."):
            continue
        if path.suffix != ".json":
            problems.append(f"news/items/{path.name}: only <id>.json files belong here")
            continue
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            problems.append(f"news/items/{path.name}: starts with a UTF-8 BOM")
            continue
        try:
            out.append((path, json.loads(raw.decode("utf-8"))))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            problems.append(f"news/items/{path.name}: not valid UTF-8 JSON ({exc})")
    if problems:
        raise NewsError(problems)
    return out


def _published_item(source: dict, image: ImageInfo | None) -> dict:
    item = {}
    for key in ITEM_ORDER:
        if key == "image":
            if image is not None:
                item["image"] = image.published(source["image"]["alt"])
        elif key in source:
            item[key] = source[key]
    return item


def build(root: Path | None = None, *, today: _dt.date | None = None) -> BuildResult:
    """Validate every source item and return the feed. Raises :class:`NewsError`.

    ``today`` only produces warnings (expired items); it never changes the
    output, so the bytes depend on the sources alone.
    """
    sources = load_sources(root)
    validator = _validator("sourceItem")
    problems: list[str] = []
    warnings: list[str] = []
    seen: dict[str, str] = {}
    images: dict[str, ImageInfo] = {}
    good: list[dict] = []

    for path, source in sources:
        where = f"news/items/{path.name}"
        errs = _schema_errors(validator, source, where)
        if errs:
            problems.extend(errs)
            continue
        item_id = source["id"]
        if path.stem != item_id:
            problems.append(f"{where}: file must be named {item_id}.json")
        if item_id in seen:
            problems.append(f"{where}: id {item_id!r} is also used by {seen[item_id]}")
        seen[item_id] = where
        date = parse_date(source["date"])
        if date is None:
            problems.append(f"{where}: date {source['date']!r} is not a real calendar date")
        if "expires" in source:
            expires = parse_date(source["expires"])
            if expires is None:
                problems.append(f"{where}: expires {source['expires']!r} is not a real calendar date")
            elif date is not None and expires < date:
                problems.append(f"{where}: expires {expires} is before its date {date}")
            elif today is not None and expires < today:
                warnings.append(f"{where}: expired on {expires}; the app hides it (delete it when convenient)")
        problems.extend(_length_problems(source, where))
        problems.extend(f"{where}: body {p}" for p in body_problems(source["body"]))

        image = None
        if "image" in source:
            name = source["image"]["file"]
            if name not in images:
                info, errs = inspect_image(img_dir(root) / name)
                problems.extend(f"{where}: {e}" for e in errs)
                if info:
                    images[name] = info
            image = images.get(name)
            if image is None:
                continue
        good.append(_published_item(source, image))

    if not sources:
        problems.append("news/items: no items; refusing to build an empty feed")
    if problems:
        raise NewsError(problems)

    folder = img_dir(root)
    if folder.is_dir():
        used = {i["image"]["url"].rsplit("/", 1)[1] for i in good if "image" in i}
        for path in sorted(folder.iterdir()):
            if path.is_file() and path.name not in used:
                warnings.append(f"news/img/{path.name}: no item uses it, but it is still published")

    # Newest first. On the same date news comes before tips, then by id, so the
    # order never depends on the file system.
    good.sort(key=lambda i: (KIND_ORDER[i["kind"]], i["id"]))
    good.sort(key=lambda i: i["date"], reverse=True)
    dropped = [i["id"] for i in good[MAX_ITEMS:]]
    kept = good[:MAX_ITEMS]
    feed = {"schema": SCHEMA, "published": f"{kept[0]['date']}T00:00:00Z", "items": kept}

    errs = validate_feed(feed)
    if errs:  # pragma: no cover - would mean this module and the schema disagree
        raise NewsError(errs)
    return BuildResult(feed=feed, dropped=dropped, warnings=warnings)


def validate_feed(feed: Any, where: str = "news.json") -> list[str]:
    """Every problem with a published feed (schema + order + uniqueness)."""
    problems = _schema_errors(_validator(), feed, where)
    if problems or not isinstance(feed, dict):
        return problems
    items = feed["items"]
    ids = [i["id"] for i in items]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problems.append(f"{where}: id {dup!r} appears more than once")
    dates = [i["date"] for i in items]
    if dates != sorted(dates, reverse=True):
        problems.append(f"{where}: items are not newest first")
    for item in items:
        if parse_date(item["date"]) is None:
            problems.append(f"{where}: {item['id']}: date {item['date']!r} is not a real calendar date")
        problems.extend(_length_problems(item, f"{where}: {item['id']}"))
        problems.extend(f"{where}: {item['id']}: body {p}" for p in body_problems(item["body"]))
    if not items:
        problems.append(f"{where}: no items")
    return problems


def canonical_bytes(feed: dict) -> bytes:
    """Exactly what :func:`write` puts on disk, and so what the signature covers."""
    return (json.dumps(feed, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def write(feed: dict, path: str | Path | None = None) -> Path:
    path = Path(path or news_path())
    util.write_json(path, feed)
    return path


def load(path: str | Path | None = None) -> dict:
    data = json.loads(Path(path or news_path()).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("news.json root must be a JSON object")
    return data
