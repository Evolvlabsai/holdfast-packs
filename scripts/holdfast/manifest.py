"""Reading, editing and checking ``manifest.json``.

The manifest is the app's single source of truth and is signed over its exact
bytes, so everything here round-trips through :func:`holdfast.util.write_json`:
two-space indent, UTF-8, LF, one trailing newline. Any tool that rewrites the
manifest must re-sign it; nothing in this repo signs outside ``publish.yml``.

Field names and which ones are required come from ``CatalogParser.ParseEntry``
in the app (``src/Holdfast.Core/Content/Catalog.cs``):

* required on a pack: ``id``, ``version``, ``url``, ``sha256``, ``size``
* required at the root: ``schema``, ``published``
* everything else is optional with a documented default

``schema/manifest.schema.json`` states the same contract for CI.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from . import util

#: Current catalog schema number (``schema`` at the manifest root).
SCHEMA = 1

#: What an unknown checksum looks like. Never a real value, and the app's
#: checksum check rejects any file against it, so a placeholder can be published
#: safely: it lists the pack without letting anything install.
PLACEHOLDER_SHA256 = "0" * 64

#: Hosts reserved for "not built yet". ``.invalid`` can never resolve (RFC 2606).
PLACEHOLDER_HOSTS = ("example.invalid", "todo.invalid")

GROUPS = ("essentials", "maps", "reference", "optional")
FORMATS = ("hfdb", "pmtiles", "zim", "hfroute", "gguf", "onnx", "zip")

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^\d{4}\.\d{2}\.\d{2}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

#: Required pack fields, exactly as the app's parser requires them.
REQUIRED_PACK_FIELDS = ("id", "version", "url", "sha256", "size")


def manifest_path(root: Path | None = None) -> Path:
    return (root or util.repo_root()) / "manifest.json"


def schema_path(root: Path | None = None) -> Path:
    return (root or util.repo_root()) / "schema" / "manifest.schema.json"


def load(path: str | Path | None = None) -> dict:
    data = json.loads(Path(path or manifest_path()).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest root must be a JSON object")
    return data


def save(data: dict, path: str | Path | None = None) -> None:
    util.write_json(path or manifest_path(), data)


def packs(data: dict) -> list[dict]:
    value = data.get("packs")
    return value if isinstance(value, list) else []


def find(data: dict, pack_id: str) -> dict | None:
    for entry in packs(data):
        if isinstance(entry, dict) and entry.get("id") == pack_id:
            return entry
    return None


def require(data: dict, pack_id: str) -> dict:
    entry = find(data, pack_id)
    if entry is None:
        known = ", ".join(str(p.get("id")) for p in packs(data))
        raise KeyError(f"no pack '{pack_id}' in the manifest (have: {known})")
    return entry


# -- placeholders ---------------------------------------------------------


def is_placeholder_sha(value: Any) -> bool:
    return not isinstance(value, str) or value == PLACEHOLDER_SHA256 or not SHA256_RE.match(value)


def is_placeholder_url(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return True
    lowered = value.lower()
    if any(host in lowered for host in PLACEHOLDER_HOSTS):
        return True
    return "todo" in lowered or "<" in value or "placeholder" in lowered


def placeholder_reasons(entry: dict) -> list[str]:
    """Every reason this pack entry is not yet publishable. Empty means real.

    ``validate_manifest.py`` reports these; it never silently accepts one.
    """
    reasons: list[str] = []
    if is_placeholder_url(entry.get("url")):
        reasons.append(f"url is a placeholder ({entry.get('url')!r})")
    if is_placeholder_sha(entry.get("sha256")):
        value = entry.get("sha256")
        shown = PLACEHOLDER_SHA256 if value == PLACEHOLDER_SHA256 else repr(value)
        reasons.append(f"sha256 is a placeholder ({shown})")
    size = entry.get("size")
    if not isinstance(size, int) or size <= 0:
        reasons.append(f"size is a placeholder ({size!r})")
    for mirror in entry.get("mirrors") or []:
        if is_placeholder_url(mirror):
            reasons.append(f"mirror is a placeholder ({mirror!r})")
    return reasons


def is_placeholder(entry: dict) -> bool:
    return bool(placeholder_reasons(entry))


# -- per-pack pipeline metadata -------------------------------------------


@dataclass
class PackMeta:
    """``packs/<id>/pack.meta.json``: what the pipeline needs and the app does not.

    Deliberately kept out of ``manifest.json``: the manifest is the app's
    contract and the app ignores fields it does not know, so build-side facts
    (who hosts it, what upstream to watch, how much it may grow) live here.
    """

    id: str
    hosting: str = "hosted"  # hosted | linked
    builder: str | None = None
    upstream: dict = None  # type: ignore[assignment]
    size_change_threshold_percent: float = 25.0
    allow_size_change: bool = False
    notes: str = ""
    raw: dict = None  # type: ignore[assignment]

    @property
    def linked(self) -> bool:
        return self.hosting == "linked"

    @property
    def hosted(self) -> bool:
        return self.hosting == "hosted"


def pack_dir(pack_id: str, root: Path | None = None) -> Path:
    return (root or util.repo_root()) / "packs" / pack_id


def load_pack_meta(pack_id: str, root: Path | None = None) -> PackMeta | None:
    path = pack_dir(pack_id, root) / "pack.meta.json"
    if not path.exists():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    return PackMeta(
        id=raw.get("id", pack_id),
        hosting=raw.get("hosting", "hosted"),
        builder=raw.get("builder"),
        upstream=raw.get("upstream") or {},
        size_change_threshold_percent=float(raw.get("sizeChangeThresholdPercent", 25.0)),
        allow_size_change=bool(raw.get("allowSizeChange", False)),
        notes=raw.get("notes", ""),
        raw=raw,
    )


def all_pack_metas(root: Path | None = None) -> dict[str, PackMeta]:
    base = (root or util.repo_root()) / "packs"
    found: dict[str, PackMeta] = {}
    if not base.exists():
        return found
    for child in sorted(base.iterdir()):
        if child.is_dir():
            meta = load_pack_meta(child.name, root)
            if meta is not None:
                found[child.name] = meta
    return found
