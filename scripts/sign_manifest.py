#!/usr/bin/env python3
"""Sign ``manifest.json`` or ``news.json`` with the Ed25519 private key. Only ``publish.yml`` runs this.

    python scripts/sign_manifest.py --key "$HOLDFAST_SIGNING_KEY"
    python scripts/sign_manifest.py --key-file /path/to/private.key --manifest manifest.json
    python scripts/sign_manifest.py --file news.json

The signature covers the file's exact bytes, so it must not be reformatted
after signing. The file is parsed and checked first: a signature over broken
JSON is worse than no signature, because the app would trust it. Which checks
apply follows from the content: a root ``items`` array is the News & tips feed
(checked against ``schema/news.schema.json``), anything else is the catalog.

Writes ``<file>.sig``: base64 of the 64-byte signature, one line. Both files
use the same key and the same signature format.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import manifest as mf  # noqa: E402
from holdfast import news, signing, util  # noqa: E402


def check_signable(path: Path) -> str:
    """Refuse (via util.fail) anything the app must not trust. Returns a summary."""
    try:
        data = mf.load(path)
    except (ValueError, UnicodeDecodeError) as exc:
        util.fail(f"{path}: not a JSON object ({exc}); refusing to sign")
    if "items" in data and "packs" not in data:
        problems = news.validate_feed(data, path.name)
        if problems:
            for problem in problems:
                print(f"error: {problem}", file=sys.stderr)
            util.fail(f"{path}: not a valid News & tips feed; refusing to sign")
        return f"{len(data['items'])} news item(s)"
    for field in ("schema", "published"):
        if field not in data:
            util.fail(f"{path}: missing required root field '{field}'; refusing to sign")
    if not mf.packs(data):
        util.fail(f"{path}: no packs; refusing to sign an empty catalog")
    return f"{len(mf.packs(data))} packs"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--manifest", "--file", dest="manifest", default=None,
        help="file to sign: manifest.json or news.json (default: manifest.json at the repo root)",
    )
    parser.add_argument("--key", default=None, help="base64 private key, or a path to a file holding it")
    parser.add_argument(
        "--key-file", default=None, help="path to a file holding the base64 private key"
    )
    parser.add_argument(
        "--env",
        default="HOLDFAST_SIGNING_KEY",
        help="environment variable to read the key from when neither --key nor --key-file is given",
    )
    parser.add_argument("--out", default=None, help="signature path (default: <manifest>.sig)")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest) if args.manifest else mf.manifest_path()
    if not manifest_path.exists():
        util.fail(f"file to sign not found: {manifest_path}")

    key_source = args.key or args.key_file or os.environ.get(args.env)
    if not key_source:
        util.fail(f"no signing key: pass --key / --key-file or set ${args.env}")

    try:
        private = signing.load_private(key_source)
    except signing.SigningError as exc:
        util.fail(str(exc))

    # Parse before signing. The app trusts whatever a valid signature covers.
    summary = check_signable(manifest_path)

    raw = manifest_path.read_bytes()
    signature = signing.sign_bytes(private, raw)
    sig_path = Path(args.out) if args.out else Path(str(manifest_path) + ".sig")
    sig_path.write_text(signing.signature_file_text(signature), encoding="utf-8", newline="\n")

    util.info(f"signed {manifest_path} ({len(raw)} bytes, {summary})")
    util.info(f"wrote  {sig_path}")
    util.info(f"public key of this signing key: {signing.public_base64(private)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
