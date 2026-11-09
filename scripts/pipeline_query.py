#!/usr/bin/env python3
"""Small questions the workflows need answered, so no YAML embeds Python.

Inline `python -c` inside an indented `run:` block is a trap: the leading
whitespace of each continuation line becomes part of the program and Python
fails with an IndentationError that only shows up when the workflow runs. Every
question the workflows ask lives here instead, where the tests can reach it.

    python scripts/pipeline_query.py pack-ids
    python scripts/pipeline_query.py meta --id core --field hosting
    python scripts/pipeline_query.py upstream-url --id shelter-repair --report upstream.json
    python scripts/pipeline_query.py public-key --env HOLDFAST_SIGNING_KEY
    python scripts/pipeline_query.py manifest-bytes

Each sub-command prints one line on success (or nothing, for an absent value)
and exits non-zero with a message on stderr when it cannot answer.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import manifest as mf  # noqa: E402
from holdfast import util  # noqa: E402


def cmd_pack_ids(args: argparse.Namespace) -> int:
    """Every pack id that has pipeline metadata, comma separated."""
    print(",".join(mf.all_pack_metas()))
    return 0


def cmd_meta(args: argparse.Namespace) -> int:
    """One field out of packs/<id>/pack.meta.json. Dots walk into objects."""
    path = mf.pack_dir(args.id) / "pack.meta.json"
    if not path.exists():
        util.fail(f"{path} not found")

    value: object = json.loads(path.read_text(encoding="utf-8"))
    for part in args.field.split("."):
        if not isinstance(value, dict) or part not in value:
            print(args.default or "")
            return 0
        value = value[part]
    print("" if value is None else value)
    return 0


def cmd_upstream_url(args: argparse.Namespace) -> int:
    """The url check_upstream.py resolved for a pack, from its JSON report."""
    report = Path(args.report)
    if not report.exists():
        print("")
        return 0
    data = json.loads(report.read_text(encoding="utf-8"))
    for check in data.get("checks", []):
        if check.get("pack_id") == args.id and check.get("url"):
            print(check["url"])
            return 0
    print("")
    return 0


def cmd_public_key(args: argparse.Namespace) -> int:
    """The base64 public key belonging to the private key in an env var.

    publish.yml uses it to verify the signature it just made the way the app
    will. The private key is never printed.
    """
    from holdfast import signing

    raw = os.environ.get(args.env)
    if not raw:
        util.fail(f"${args.env} is not set")
    try:
        print(signing.public_base64(signing.load_private(raw)))
    except signing.SigningError as exc:
        util.fail(f"${args.env} is not a usable Ed25519 private key: {exc}")
    return 0


def cmd_manifest_bytes(args: argparse.Namespace) -> int:
    """Fail if manifest.json's bytes are not what a signature can safely cover.

    CRLF, a BOM or a missing final newline all make the signed bytes depend on
    the machine that checked the repository out.
    """
    path = Path(args.manifest) if args.manifest else mf.manifest_path()
    raw = path.read_bytes()
    problems = []
    if b"\r\n" in raw:
        problems.append("contains CRLF line endings")
    if raw.startswith(b"\xef\xbb\xbf"):
        problems.append("starts with a UTF-8 BOM, which would be signed too")
    if not raw.endswith(b"}\n"):
        problems.append("does not end with '}' and exactly one newline")
    if problems:
        for problem in problems:
            print(f"error: {path.name} {problem}", file=sys.stderr)
        return 1
    print(f"{path.name} is {len(raw)} bytes, LF, no BOM: these are the bytes publish.yml signs")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("pack-ids", help="comma-separated pack ids that have pack.meta.json")

    meta = sub.add_parser("meta", help="read one field from a pack's pack.meta.json")
    meta.add_argument("--id", required=True)
    meta.add_argument("--field", required=True, help="field name, dots for nesting (e.g. upstream.kind)")
    meta.add_argument("--default", default="")

    upstream = sub.add_parser("upstream-url", help="the url check_upstream.py resolved for a pack")
    upstream.add_argument("--id", required=True)
    upstream.add_argument("--report", default="upstream.json")

    pub = sub.add_parser("public-key", help="base64 public key for the private key in an env var")
    pub.add_argument("--env", default="HOLDFAST_SIGNING_KEY")

    bytes_cmd = sub.add_parser("manifest-bytes", help="check the manifest's bytes are signable")
    bytes_cmd.add_argument("--manifest", default=None)

    args = parser.parse_args(argv)
    return {
        "pack-ids": cmd_pack_ids,
        "meta": cmd_meta,
        "upstream-url": cmd_upstream_url,
        "public-key": cmd_public_key,
        "manifest-bytes": cmd_manifest_bytes,
    }[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
