"""Quick cards and survival skills written as Markdown, one file (or folder) each.

This is the format contributors edit in pull requests. CONTRIBUTING.md describes it
for people; this module is the rule book the build and the tests share.

A quick card is ``packs/core/sources/cards/<id>.md``::

    ---
    id: choking
    title: Choking
    lead: Can't cough, speak or breathe? Act now.
    tone: normal
    icon: alert
    order: 70
    source: American Red Cross choking first aid
    status: reviewed
    reviewed: 2026-11-16
    ---

    ## Ask: are you choking?

    If they can cough hard or speak, let them keep coughing.

A survival skill is a folder ``packs/core/sources/skills/<id>/`` holding
``skill.md`` and its line drawings (``*.svg``). Its steps may start with one
picture line, ``![What the picture shows.](file.svg)``.

Standard library only (plus defusedxml, already pinned), like the rest of the
pipeline: these files come from strangers, so the parser is strict and small.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from dataclasses import dataclass
from pathlib import Path

from defusedxml import ElementTree as SafeET

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KEY_RE = re.compile(r"^([a-z][a-zA-Z]*):(?: (.*))?$")
IMAGE_RE = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)\)$")

STATUSES = ("draft", "reviewed")
TONES = ("normal", "danger")
# Glyphs the app can draw for a card (src/Holdfast.App/Controls/Icons.cs in holdfast-app).
# An app that does not know a glyph shows an info icon, so add new ones there first.
CARD_ICONS = ("alert", "bolt", "cold", "compass", "drop", "flame", "heart", "info", "pill", "plus",
              "shelter", "shield-alert", "signal", "sun", "timer", "water")
TIMERS = ("tourniquet",)
SKILL_CATEGORIES = ("light", "fire", "cooking", "water", "shelter", "signals", "sanitation", "knots", "warmth")
# Projects in these categories involve flame or fuel: each must carry at least one warning.
WARNING_CATEGORIES = ("light", "fire", "cooking", "warmth")
DIFFICULTIES = ("easy", "medium", "hard")
# Quick cards never give a medicine dose (spec: Licensing and content safety).
DOSE_WORDS = ("mg", "milligram", "ml of", "tablet", "capsule", "dose of")

LIMITS = {
    "title": 40,       # a two-line Home tile
    "lead": 120,
    "summary": 160,
    "step_title": 50,
    "step_body": 400,
    "alt": 200,
}

# Line drawings: a small, safe subset of SVG the app draws as tinted paths.
SVG_NS = "http://www.w3.org/2000/svg"
SVG_VIEWBOX = "0 0 240 160"
SVG_MAX_BYTES = 40_000
SVG_ROOT_ATTRS = {"xmlns", "viewBox", "width", "height", "fill", "stroke", "stroke-width",
                  "stroke-linecap", "stroke-linejoin"}
SVG_PATH_ATTRS = {"d", "class", "fill", "stroke", "stroke-width"}
SVG_PATH_CLASSES = ("accent", "water", "solid")
SVG_PATH_DATA_RE = re.compile(r"^[MmLlHhVvCcSsQqTtAaZz0-9eE.,+\-\s]+$")


class ContentError(ValueError):
    """A content file breaks the format. The message names the file and says what to fix."""


@dataclass(frozen=True)
class Step:
    title: str
    body: str
    image: str | None = None
    alt: str | None = None


# ---------------------------------------------------------------------------
# Front matter and steps


def split_front_matter(text: str, where: str) -> tuple[dict, list[str]]:
    """Returns the front matter as a dict and the body as lines.

    Front matter is ``key: value`` lines, or ``key:`` followed by ``  - item`` lines
    for a list. Nothing else: no nesting, no comments, no YAML tricks.
    """
    lines = text.replace("\r\n", "\n").lstrip("﻿").split("\n")
    if not lines or lines[0].strip() != "---":
        raise ContentError(f"{where}: must start with a '---' line (the front matter)")
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        raise ContentError(f"{where}: the front matter has no closing '---' line") from None

    meta: dict[str, object] = {}
    current_list: list[str] | None = None
    for n in range(1, end):
        line = lines[n]
        if not line.strip():
            continue
        if line.startswith("  - ") or line.startswith("- "):
            if current_list is None:
                raise ContentError(f"{where}:{n + 1}: a '- item' line must follow a 'key:' line")
            current_list.append(_unquote(line.split("- ", 1)[1].strip()))
            continue
        match = KEY_RE.match(line)
        if not match:
            raise ContentError(f"{where}:{n + 1}: expected 'key: value', got {line!r}")
        key, value = match.group(1), (match.group(2) or "").strip()
        if key in meta:
            raise ContentError(f"{where}:{n + 1}: '{key}' appears twice")
        if value:
            meta[key] = _unquote(value)
            current_list = None
        else:
            current_list = []
            meta[key] = current_list
    # A 'key:' with no items is an empty value, not an empty list.
    meta = {k: (None if v == [] else v) for k, v in meta.items()}
    return meta, lines[end + 1:]


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return value[1:-1]
    return value


def parse_steps(body: list[str], where: str, *, allow_images: bool) -> list[Step]:
    """``## Step title`` headings, each followed by one paragraph (and, for skills, one picture)."""
    steps: list[tuple[str, list[str]]] = []
    for n, line in enumerate(body):
        if line.startswith("## "):
            steps.append((line[3:].strip(), []))
        elif line.startswith("#"):
            raise ContentError(f"{where}: only '## ' headings are allowed, one per step (got {line!r})")
        elif line.strip():
            if not steps:
                raise ContentError(f"{where}: text before the first '## ' step heading: {line.strip()!r}")
            steps[-1][1].append(line.strip())
        elif steps and steps[-1][1] and steps[-1][1][-1] != "":
            steps[-1][1].append("")

    result = []
    for title, raw in steps:
        lines = list(raw)
        while lines and lines[-1] == "":
            lines.pop()
        image = alt = None
        if lines and IMAGE_RE.match(lines[0]):
            if not allow_images:
                raise ContentError(f"{where}: step '{title}': quick cards have no pictures")
            alt, image = IMAGE_RE.match(lines[0]).groups()
            lines = lines[1:]
            while lines and lines[0] == "":
                lines.pop(0)
        if any(IMAGE_RE.match(ln) for ln in lines):
            raise ContentError(f"{where}: step '{title}': a picture must be the first line under its heading")
        if "" in lines:
            raise ContentError(f"{where}: step '{title}': keep each step to one paragraph")
        text = " ".join(lines).strip()
        if not title:
            raise ContentError(f"{where}: a step heading is empty")
        if not text:
            raise ContentError(f"{where}: step '{title}' has no text under it")
        result.append(Step(title, text, image, alt))
    return result


# ---------------------------------------------------------------------------
# Field checks


def _require(meta: dict, key: str, where: str) -> str:
    value = meta.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ContentError(f"{where}: '{key}' is required")
    return value.strip()


def _one_of(meta: dict, key: str, allowed: tuple[str, ...], where: str, *, required: bool = True) -> str | None:
    value = meta.get(key)
    if value is None and not required:
        return None
    if value not in allowed:
        raise ContentError(f"{where}: '{key}' must be one of {', '.join(allowed)} (got {value!r})")
    return value


def _length(value: str, limit_key: str, label: str, where: str) -> None:
    if len(value) > LIMITS[limit_key]:
        raise ContentError(f"{where}: {label} is {len(value)} characters; keep it to {LIMITS[limit_key]}")


def _order(meta: dict, where: str) -> int:
    value = meta.get("order")
    if not isinstance(value, str) or not value.isdigit():
        raise ContentError(f"{where}: 'order' must be a whole number (it sets the place in the list)")
    return int(value)


def _status(meta: dict, where: str) -> tuple[str, str | None]:
    status = _one_of(meta, "status", STATUSES, where)
    reviewed = meta.get("reviewed")
    if status == "reviewed":
        try:
            _dt.date.fromisoformat(str(reviewed))
        except ValueError:
            raise ContentError(f"{where}: 'status: reviewed' needs 'reviewed: YYYY-MM-DD' (the review date)") from None
    elif reviewed:
        raise ContentError(f"{where}: a draft has no 'reviewed' date yet; remove it")
    return status, reviewed


def _check_id(meta: dict, expected: str, where: str) -> str:
    ident = _require(meta, "id", where)
    if not ID_RE.match(ident):
        raise ContentError(f"{where}: 'id' must be lower-case words joined by hyphens (got {ident!r})")
    if ident != expected:
        raise ContentError(f"{where}: 'id' is {ident!r} but its file or folder is named {expected!r}; make them match")
    return ident


def _known_keys(meta: dict, allowed: set[str], where: str) -> None:
    unknown = sorted(set(meta) - allowed)
    if unknown:
        raise ContentError(f"{where}: unknown field(s): {', '.join(unknown)}")


# ---------------------------------------------------------------------------
# Quick cards

CARD_KEYS = {"id", "title", "lead", "tone", "icon", "timer", "order", "source", "status", "reviewed"}


def load_card(path: Path) -> dict:
    """One card file as the dict the pack builders take (cards.json shape) plus order/status/reviewed."""
    where = str(path)
    meta, body = split_front_matter(path.read_text(encoding="utf-8"), where)
    _known_keys(meta, CARD_KEYS, where)
    ident = _check_id(meta, path.stem, where)
    title = _require(meta, "title", where)
    lead = _require(meta, "lead", where)
    source = _require(meta, "source", where)
    _length(title, "title", "the title", where)
    _length(lead, "lead", "the lead", where)
    status, reviewed = _status(meta, where)
    steps = parse_steps(body, where, allow_images=False)
    if not 3 <= len(steps) <= 8:
        raise ContentError(f"{where}: a quick card has 3 to 8 steps (this one has {len(steps)})")
    for step in steps:
        _length(step.title, "step_title", f"step '{step.title}' title", where)
        _length(step.body, "step_body", f"step '{step.title}'", where)
        lowered = f" {step.body.lower()} "
        for word in DOSE_WORDS:
            if re.search(rf"(?<![a-z]){re.escape(word)}(?![a-z])", lowered):
                raise ContentError(f"{where}: step '{step.title}' gives a medicine dose ({word!r}); cards never do")

    return {
        "id": ident,
        "title": title,
        "lead": lead,
        "tone": _one_of(meta, "tone", TONES, where),
        "icon": _one_of(meta, "icon", CARD_ICONS, where),
        "source": source,
        "timer": _one_of(meta, "timer", TIMERS, where, required=False),
        "draft": status != "reviewed",
        "steps": [{"title": s.title, "body": s.body} for s in steps],
        "order": _order(meta, where),
        "status": status,
        "reviewed": reviewed,
    }


def load_cards(folder: Path) -> list[dict]:
    """Every card in ``folder``, in list order. Ids and order numbers must be unique."""
    cards = [load_card(p) for p in sorted(folder.glob("*.md")) if p.name.lower() != "readme.md"]
    _unique(cards, "id", folder)
    _unique(cards, "order", folder)
    return sorted(cards, key=lambda c: c["order"])


def card_for_pack(card: dict) -> dict:
    """The card as the app reads it: the review bookkeeping stays in the repo."""
    return {k: v for k, v in card.items() if k not in ("order", "status", "reviewed")}


def card_to_markdown(card: dict, *, order: int, reviewed: str | None) -> str:
    """Writes a card in the file format (used once, to move cards.json over; kept for tools)."""
    lines = ["---", f"id: {card['id']}", f"title: {card['title']}", f"lead: {card['lead']}",
             f"tone: {card['tone']}", f"icon: {card['icon']}"]
    if card.get("timer"):
        lines.append(f"timer: {card['timer']}")
    lines += [f"order: {order}", f"source: {card['source']}"]
    if card.get("draft"):
        lines.append("status: draft")
    else:
        lines += ["status: reviewed", f"reviewed: {reviewed}"]
    lines.append("---")
    for step in card["steps"]:
        lines += ["", f"## {step['title']}", "", step["body"]]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Survival skills

SKILL_KEYS = {"id", "title", "summary", "category", "difficulty", "time", "order", "needs", "warnings",
              "source", "status", "reviewed"}


def load_skill(folder: Path) -> dict:
    where = str(folder / "skill.md")
    path = folder / "skill.md"
    if not path.is_file():
        raise ContentError(f"{folder}: a skill folder needs a skill.md")
    meta, body = split_front_matter(path.read_text(encoding="utf-8"), where)
    _known_keys(meta, SKILL_KEYS, where)
    ident = _check_id(meta, folder.name, where)
    title = _require(meta, "title", where)
    summary = _require(meta, "summary", where)
    _length(title, "title", "the title", where)
    _length(summary, "summary", "the summary", where)
    category = _one_of(meta, "category", SKILL_CATEGORIES, where)
    needs = _list(meta, "needs", where, required=True)
    warnings = _list(meta, "warnings", where, required=category in WARNING_CATEGORIES)
    status, reviewed = _status(meta, where)
    steps = parse_steps(body, where, allow_images=True)
    if not 2 <= len(steps) <= 10:
        raise ContentError(f"{where}: a skill has 2 to 10 steps (this one has {len(steps)})")

    used = set()
    for step in steps:
        _length(step.title, "step_title", f"step '{step.title}' title", where)
        _length(step.body, "step_body", f"step '{step.title}'", where)
        if step.image is None:
            continue
        if not step.alt or not step.alt.strip():
            raise ContentError(f"{where}: step '{step.title}': the picture needs a description in the [brackets]")
        _length(step.alt, "alt", f"step '{step.title}' picture description", where)
        if "/" in step.image or "\\" in step.image or not step.image.endswith(".svg"):
            raise ContentError(f"{where}: step '{step.title}': pictures are .svg files in the skill's own folder")
        check_svg(folder / step.image)
        used.add(step.image)

    extra = sorted(p.name for p in folder.iterdir() if p.name != "skill.md" and p.name not in used)
    if extra:
        raise ContentError(f"{folder}: files no step uses: {', '.join(extra)}")

    return {
        "id": ident,
        "title": title,
        "summary": summary,
        "category": category,
        "difficulty": _one_of(meta, "difficulty", DIFFICULTIES, where),
        "time": _require(meta, "time", where),
        "needs": needs,
        "warnings": warnings or [],
        "source": _require(meta, "source", where),
        "steps": [{"title": s.title, "body": s.body, "image": s.image, "alt": s.alt} for s in steps],
        "order": _order(meta, where),
        "status": status,
        "reviewed": reviewed,
        "draft": status != "reviewed",
    }


def load_skills(folder: Path) -> list[dict]:
    if not folder.is_dir():
        return []
    skills = [load_skill(p) for p in sorted(folder.iterdir()) if p.is_dir()]
    _unique(skills, "id", folder)
    _unique(skills, "order", folder)
    return sorted(skills, key=lambda s: s["order"])


def _list(meta: dict, key: str, where: str, *, required: bool) -> list[str] | None:
    value = meta.get(key)
    if value is None:
        if required:
            raise ContentError(f"{where}: '{key}' needs at least one '  - item' line")
        return None
    if not isinstance(value, list) or not all(isinstance(v, str) and v.strip() for v in value):
        raise ContentError(f"{where}: '{key}' must be a list of '  - item' lines")
    return [v.strip() for v in value]


def _unique(items: list[dict], key: str, where: Path) -> None:
    seen: dict[object, str] = {}
    for item in items:
        if item[key] in seen:
            raise ContentError(f"{where}: {seen[item[key]]} and {item['id']} share {key} {item[key]!r}")
        seen[item[key]] = item["id"]


# ---------------------------------------------------------------------------
# Line drawings


def check_svg(path: Path) -> None:
    """A drawing is plain paths on a 240 x 160 box. No scripts, links, images, text or styles."""
    where = str(path)
    if not path.is_file():
        raise ContentError(f"{where}: the picture file is missing")
    data = path.read_bytes()
    if len(data) > SVG_MAX_BYTES:
        raise ContentError(f"{where}: {len(data)} bytes; keep a drawing under {SVG_MAX_BYTES}")
    try:
        root = SafeET.fromstring(data)
    except Exception as exc:  # defusedxml raises several types; any of them means "not safe XML"
        raise ContentError(f"{where}: not a valid, safe SVG file ({exc})") from None

    if root.tag != f"{{{SVG_NS}}}svg":
        raise ContentError(f"{where}: the root must be <svg xmlns=\"{SVG_NS}\">")
    _attrs(root, SVG_ROOT_ATTRS, where)
    if root.get("viewBox") != SVG_VIEWBOX:
        raise ContentError(f"{where}: viewBox must be \"{SVG_VIEWBOX}\"")

    paths = 0
    for child in root:
        tag = child.tag.split("}", 1)[-1]
        if tag == "title":
            if len(child):
                raise ContentError(f"{where}: <title> holds text only")
            continue
        if tag != "path":
            raise ContentError(f"{where}: only <title> and <path> are allowed (found <{tag}>)")
        if len(child):
            raise ContentError(f"{where}: a <path> has no children")
        _attrs(child, SVG_PATH_ATTRS, where)
        d = child.get("d") or ""
        if not d.strip() or not SVG_PATH_DATA_RE.match(d):
            raise ContentError(f"{where}: a <path> needs plain path data in 'd'")
        cls = child.get("class")
        if cls is not None and cls not in SVG_PATH_CLASSES:
            raise ContentError(f"{where}: path class must be one of {', '.join(SVG_PATH_CLASSES)} (got {cls!r})")
        paths += 1
    if paths == 0:
        raise ContentError(f"{where}: the drawing has no <path>")


def _attrs(element, allowed: set[str], where: str) -> None:
    for name in element.attrib:
        bare = name.split("}", 1)[-1]
        if bare not in allowed:
            raise ContentError(f"{where}: attribute '{bare}' is not allowed on <{element.tag.split('}', 1)[-1]}>")


# ---------------------------------------------------------------------------


def write_cards_json(cards: list[dict], out: Path, *, include_drafts: bool = False) -> list[str]:
    """Writes the cards the app should get to ``out``. Returns the ids of drafts left out."""
    shipped = [card_for_pack(c) for c in cards if include_drafts or not c["draft"]]
    skipped = [c["id"] for c in cards if c["draft"] and not include_drafts]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(shipped, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return skipped
