"""Conditional HTTP: HEAD probes and ETag / Last-Modified cached downloads.

Upstream checks must not re-download hundreds of megabytes to learn that nothing
changed, so every fetch here is conditional and the validators are kept in a
small JSON cache file next to the downloads
(``.cache/http.json`` by default, gitignored).

Standard library only (``urllib``).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

USER_AGENT = "holdfast-packs/1.0 (+https://github.com/Evolvlabsai/holdfast-packs) python-urllib"

DEFAULT_TIMEOUT = 60


@dataclass
class HeadResult:
    """What a HEAD (or a GET fallback) told us about a URL."""

    url: str
    ok: bool
    status: int | None = None
    etag: str | None = None
    last_modified: str | None = None
    length: int | None = None
    error: str | None = None
    final_url: str | None = None

    def validator(self) -> str:
        return self.etag or self.last_modified or ""


@dataclass
class Cache:
    """Validators remembered per URL, so a check can say "unchanged"."""

    path: Path
    entries: dict[str, dict] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path) -> "Cache":
        p = Path(path)
        if p.exists():
            try:
                return cls(p, json.loads(p.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass
        return cls(p, {})

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def get(self, url: str) -> dict:
        return self.entries.get(url, {})

    def remember(self, url: str, *, etag: str | None, last_modified: str | None, length: int | None, path: str | None = None) -> None:
        entry = {k: v for k, v in {
            "etag": etag,
            "lastModified": last_modified,
            "length": length,
            "path": path,
        }.items() if v is not None}
        self.entries[url] = entry

    def changed(self, url: str, head: HeadResult) -> bool | None:
        """True / False, or None when we have nothing to compare against."""
        known = self.get(url)
        if not known:
            return None
        if head.etag and known.get("etag"):
            return head.etag != known["etag"]
        if head.last_modified and known.get("lastModified"):
            return head.last_modified != known["lastModified"]
        if head.length is not None and known.get("length") is not None:
            return head.length != known["length"]
        return None


def _request(url: str, method: str, headers: dict[str, str] | None = None) -> urllib.request.Request:
    req = urllib.request.Request(url, method=method)
    req.add_header("User-Agent", USER_AGENT)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    return req


def head(url: str, *, timeout: int = DEFAULT_TIMEOUT, allow_get_fallback: bool = True) -> HeadResult:
    """HEAD a URL. Falls back to a ranged GET for hosts that refuse HEAD."""
    try:
        with urllib.request.urlopen(_request(url, "HEAD"), timeout=timeout) as resp:
            return _from_response(url, resp)
    except urllib.error.HTTPError as exc:
        if allow_get_fallback and exc.code in (403, 405, 501):
            return _ranged_get(url, timeout=timeout)
        return HeadResult(url, ok=False, status=exc.code, error=f"HTTP {exc.code} {exc.reason}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if allow_get_fallback:
            fallback = _ranged_get(url, timeout=timeout)
            if fallback.ok:
                return fallback
        return HeadResult(url, ok=False, error=str(exc))


def _ranged_get(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> HeadResult:
    try:
        with urllib.request.urlopen(_request(url, "GET", {"Range": "bytes=0-0"}), timeout=timeout) as resp:
            result = _from_response(url, resp)
            # A 206 reports the one byte we asked for; recover the real length.
            total = resp.headers.get("Content-Range", "")
            if "/" in total:
                tail = total.rsplit("/", 1)[1].strip()
                result.length = int(tail) if tail.isdigit() else None
            elif resp.status == 206:
                result.length = None
            return result
    except urllib.error.HTTPError as exc:
        return HeadResult(url, ok=False, status=exc.code, error=f"HTTP {exc.code} {exc.reason}")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return HeadResult(url, ok=False, error=str(exc))


def _from_response(url: str, resp) -> HeadResult:
    length = resp.headers.get("Content-Length")
    return HeadResult(
        url=url,
        ok=200 <= resp.status < 300,
        status=resp.status,
        etag=resp.headers.get("ETag"),
        last_modified=resp.headers.get("Last-Modified"),
        length=int(length) if length and length.isdigit() else None,
        final_url=resp.geturl(),
    )


def get_text(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> str:
    with urllib.request.urlopen(_request(url, "GET"), timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def download(url: str, dest: str | Path, *, cache: Cache | None = None, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Download ``url`` to ``dest`` unless the cached validator still matches.

    Returns True when bytes were written, False when the server answered 304 or
    the cached copy is still current. The file is written to ``<dest>.part`` and
    renamed, so an interrupted run never leaves a short file behind.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    known = cache.get(url) if cache else {}

    headers: dict[str, str] = {}
    if dest.exists() and known:
        if known.get("etag"):
            headers["If-None-Match"] = known["etag"]
        elif known.get("lastModified"):
            headers["If-Modified-Since"] = known["lastModified"]

    try:
        with urllib.request.urlopen(_request(url, "GET", headers), timeout=timeout) as resp:
            if resp.status == 304:
                return False
            part = dest.with_suffix(dest.suffix + ".part")
            with open(part, "wb") as fh:
                while block := resp.read(1 << 20):
                    fh.write(block)
            part.replace(dest)
            if cache is not None:
                cache.remember(
                    url,
                    etag=resp.headers.get("ETag"),
                    last_modified=resp.headers.get("Last-Modified"),
                    length=dest.stat().st_size,
                    path=str(dest),
                )
            return True
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return False
        raise
