#!/usr/bin/env python3
"""Generate the project's Ed25519 manifest signing key pair. Run this once, ever.

    python scripts/keygen.py --out "$TMPDIR/holdfast-keys"

Writes ``private.key`` and ``public.key`` (both base64, one line each) into a
directory **outside the repository** and prints what to do with them.

The private key must never be committed, never leave your password manager and
GitHub Secrets, and never be regenerated casually: the public half is compiled
into shipped apps, so a new key makes every installed app reject every future
manifest until it is updated.
"""

from __future__ import annotations

import argparse
import os
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import signing, util  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, help="directory for private.key and public.key (keep it OUT of the repo)")
    parser.add_argument("--force", action="store_true", help="overwrite an existing private.key")
    args = parser.parse_args(argv)

    out = Path(args.out).resolve()
    repo = util.repo_root()
    if out == repo or repo in out.parents:
        util.fail(
            f"{out} is inside the repository ({repo}). Write keys to a directory outside it, "
            "for example a temp folder or an encrypted volume."
        )

    out.mkdir(parents=True, exist_ok=True)
    private_path = out / "private.key"
    public_path = out / "public.key"
    if private_path.exists() and not args.force:
        util.fail(f"{private_path} already exists. Refusing to overwrite a signing key (use --force if you are sure).")

    private_b64, public_b64 = signing.generate()
    private_path.write_text(private_b64 + "\n", encoding="utf-8", newline="\n")
    public_path.write_text(public_b64 + "\n", encoding="utf-8", newline="\n")
    if os.name == "posix":
        private_path.chmod(stat.S_IRUSR | stat.S_IWUSR)

    util.info(f"private key: {private_path}")
    util.info(f"public key:  {public_path}")
    util.info("")
    util.info(f"public key (base64): {public_b64}")
    util.info("")
    util.info("Next:")
    util.info("  1. Store the private key in the repo secret HOLDFAST_SIGNING_KEY")
    util.info("     (Settings -> Secrets and variables -> Actions -> New repository secret),")
    util.info("     and keep one copy in your password manager. Nowhere else.")
    util.info("  2. Put the public key base64 above into HoldfastConfig.PublicKeyBase64 in the app repo.")
    util.info("  3. Delete the private.key file from disk once both are done:")
    util.info(f"     rm {private_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
