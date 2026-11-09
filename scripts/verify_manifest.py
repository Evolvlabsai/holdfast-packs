#!/usr/bin/env python3
"""Verify ``manifest.json.sig`` against ``manifest.json`` with the public key.

    python scripts/verify_manifest.py --pub <base64 public key>
    python scripts/verify_manifest.py --pub public.key --manifest manifest.json

Exit 0 only when the signature is a valid Ed25519 signature over the manifest's
exact bytes -- the same check the app makes before it trusts a catalog. Run it
after signing and after any publish step that copies files around: a reformatted
or re-encoded manifest fails here rather than on someone's phone.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import manifest as mf  # noqa: E402
from holdfast import signing, util  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--manifest", default=None, help="path to manifest.json (default: repo root)")
    parser.add_argument("--sig", default=None, help="path to the signature (default: <manifest>.sig)")
    parser.add_argument("--pub", default=None, help="base64 public key, or a path to a file holding it")
    parser.add_argument("--env", default="HOLDFAST_PUBLIC_KEY", help="environment variable fallback for the public key")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest) if args.manifest else mf.manifest_path()
    sig_path = Path(args.sig) if args.sig else Path(str(manifest_path) + ".sig")

    if not manifest_path.exists():
        util.fail(f"manifest not found: {manifest_path}")
    if not sig_path.exists():
        util.fail(f"signature not found: {sig_path}")

    pub_source = args.pub or os.environ.get(args.env)
    if not pub_source:
        util.fail(f"no public key: pass --pub or set ${args.env}")

    try:
        public = signing.load_public(pub_source)
    except signing.SigningError as exc:
        util.fail(str(exc))

    ok = signing.verify_bytes(public, manifest_path.read_bytes(), sig_path.read_bytes())
    if not ok:
        util.info("signature INVALID")
        util.info("The app would ignore this catalog and keep the last good one.")
        return 1

    data = mf.load(manifest_path)
    util.info("signature OK")
    util.info(
        f"schema {data.get('schema')}, published {data.get('published')}, "
        f"{len(mf.packs(data))} pack(s), minAppVersion {data.get('minAppVersion')}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
