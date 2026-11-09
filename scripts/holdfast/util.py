"""Small shared helpers: hashing, sizes, dates, subprocess, logging."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    # Pack names, licences and snippets carry em dashes and ellipses. On a
    # Windows console the default code page cannot encode them and printing
    # would raise UnicodeEncodeError mid-build.
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[union-attr]
    except (AttributeError, OSError, ValueError):  # pragma: no cover - depends on the host
        pass

#: Date-based pack version, e.g. ``2026.11.09``.
VERSION_FORMAT = "%Y.%m.%d"

#: ``published`` on a pack entry (the app parses ``yyyy-MM-dd`` exactly).
DATE_FORMAT = "%Y-%m-%d"


def today() -> _dt.date:
    return _dt.datetime.now(_dt.UTC).date()


def version_today() -> str:
    return today().strftime(VERSION_FORMAT)


def iso_date(value: _dt.date | None = None) -> str:
    return (value or today()).strftime(DATE_FORMAT)


def iso_timestamp(value: _dt.datetime | None = None) -> str:
    """The exact root ``published`` shape the app writes and reads: ``…THH:mm:ssZ``."""
    moment = (value or _dt.datetime.now(_dt.UTC)).astimezone(_dt.UTC)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path: str | Path, chunk: int = 1 << 20) -> str:
    """Lower-case hex SHA-256, streamed so multi-GB packs do not land in memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while block := fh.read(chunk):
            digest.update(block)
    return digest.hexdigest()


def size_and_sha256(path: str | Path) -> tuple[int, str]:
    p = Path(path)
    return p.stat().st_size, sha256_file(p)


def human_bytes(value: int | None) -> str:
    if value is None:
        return "?"
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size) < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:,.1f} {unit}"
        size /= 1024
    return f"{size:,.1f} TB"


def read_json(path: str | Path) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, value: object) -> None:
    """Pretty JSON with a trailing newline and LF endings everywhere.

    The manifest is signed over its exact bytes, so how it is written matters:
    two-space indent, no trailing spaces, ``\\n`` endings, UTF-8, no BOM.
    """
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    Path(path).write_bytes(text.encode("utf-8"))


def info(message: str) -> None:
    print(message, flush=True)


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr, flush=True)


def fail(message: str, code: int = 1) -> None:
    print(f"error: {message}", file=sys.stderr, flush=True)
    raise SystemExit(code)


def require_tool(name: str, install_hint: str) -> str:
    """Resolve an external CLI or exit with the install instructions."""
    found = shutil.which(name)
    if not found:
        fail(f"'{name}' is not on PATH. {install_hint}")
    return found  # type: ignore[return-value]


def run(cmd: list[str], *, cwd: str | Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command, echoing it first. Never uses a shell."""
    info("$ " + " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, check=check, text=True)


def repo_root() -> Path:
    """The repository root, found from this file (scripts/holdfast/util.py)."""
    return Path(__file__).resolve().parents[2]
