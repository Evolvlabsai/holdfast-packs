"""Ed25519 signing of ``manifest.json``, in the exact shape the app accepts.

The app (``CatalogVerifier`` in ``src/Holdfast.Core/Content/CatalogVerifier.cs``):

* holds a 32-byte Ed25519 **public** key, compiled in as base64;
* reads ``manifest.json.sig`` as either the raw 64 signature bytes or base64
  text with whitespace allowed, and rejects anything else;
* verifies the signature over the **exact bytes** of ``manifest.json`` -- not a
  re-serialisation, not a canonical form. Re-indenting the file invalidates it.

So this module signs ``Path.read_bytes()`` and nothing else, and writes the
signature as base64 plus one newline -- what the app accepts and what
``tools/Holdfast.PackTool sign`` already writes, so the two interoperate.

Private key file format: base64 of the 32-byte seed (one line). That is what
``keygen.py`` writes and what goes into the ``HOLDFAST_SIGNING_KEY`` secret.
"""

from __future__ import annotations

import base64
import binascii
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

PRIVATE_KEY_LENGTH = 32
PUBLIC_KEY_LENGTH = 32
SIGNATURE_LENGTH = 64

#: Max size of a signature file the app will even look at.
MAX_SIG_FILE_BYTES = 512


class SigningError(RuntimeError):
    """A key or signature was not in a usable form."""


def _strip(text: str) -> str:
    """Drop all whitespace, matching ``CatalogVerifier.Strip``."""
    return "".join(ch for ch in text if not ch.isspace())


def decode_base64(text: str, expected: int, what: str) -> bytes:
    try:
        raw = base64.b64decode(_strip(text), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise SigningError(f"{what} is not valid base64") from exc
    if len(raw) != expected:
        raise SigningError(f"{what} must be {expected} bytes, got {len(raw)}")
    return raw


def generate() -> tuple[str, str]:
    """A new key pair as ``(private_base64, public_base64)``."""
    private = Ed25519PrivateKey.generate()
    seed = private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return base64.b64encode(seed).decode(), base64.b64encode(public_bytes(private)).decode()


def public_bytes(private: Ed25519PrivateKey) -> bytes:
    return private.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )


def load_private(text_or_path: str) -> Ed25519PrivateKey:
    """Accept the key itself (base64) or a path to a file holding it."""
    candidate = Path(text_or_path)
    try:
        if candidate.exists() and candidate.is_file():
            text_or_path = candidate.read_text(encoding="utf-8")
    except OSError:
        pass
    seed = decode_base64(text_or_path, PRIVATE_KEY_LENGTH, "private key")
    return Ed25519PrivateKey.from_private_bytes(seed)


def load_public(text_or_path: str) -> Ed25519PublicKey:
    candidate = Path(text_or_path)
    try:
        if candidate.exists() and candidate.is_file():
            text_or_path = candidate.read_text(encoding="utf-8")
    except OSError:
        pass
    raw = decode_base64(text_or_path, PUBLIC_KEY_LENGTH, "public key")
    return Ed25519PublicKey.from_public_bytes(raw)


def public_base64(private: Ed25519PrivateKey) -> str:
    return base64.b64encode(public_bytes(private)).decode()


def sign_bytes(private: Ed25519PrivateKey, data: bytes) -> bytes:
    return private.sign(data)


def signature_file_text(signature: bytes) -> str:
    """The contents of ``manifest.json.sig``: base64 plus one newline."""
    if len(signature) != SIGNATURE_LENGTH:
        raise SigningError(f"an Ed25519 signature is {SIGNATURE_LENGTH} bytes, got {len(signature)}")
    return base64.b64encode(signature).decode() + "\n"


def read_signature_file(data: bytes) -> bytes:
    """Parse a ``.sig`` file the way the app does: raw 64 bytes or base64 text."""
    if len(data) == SIGNATURE_LENGTH:
        return data
    if not data or len(data) > MAX_SIG_FILE_BYTES:
        raise SigningError(f"signature file is {len(data)} bytes; expected 64 raw bytes or base64 text")
    return decode_base64(data.decode("utf-8", errors="strict"), SIGNATURE_LENGTH, "signature")


def verify_bytes(public: Ed25519PublicKey, data: bytes, signature_file_bytes: bytes) -> bool:
    """True only when the signature covers exactly ``data``."""
    try:
        signature = read_signature_file(signature_file_bytes)
    except (SigningError, UnicodeDecodeError):
        return False
    try:
        public.verify(signature, data)
        return True
    except InvalidSignature:
        return False


def sign_file(private: Ed25519PrivateKey, manifest: str | Path) -> Path:
    """Sign ``manifest`` and write ``<manifest>.sig`` beside it."""
    manifest = Path(manifest)
    signature = sign_bytes(private, manifest.read_bytes())
    sig_path = Path(str(manifest) + ".sig")
    sig_path.write_text(signature_file_text(signature), encoding="utf-8", newline="\n")
    return sig_path


def verify_file(public: Ed25519PublicKey, manifest: str | Path, sig: str | Path | None = None) -> bool:
    manifest = Path(manifest)
    sig_path = Path(sig) if sig else Path(str(manifest) + ".sig")
    if not sig_path.exists():
        raise SigningError(f"signature not found: {sig_path}")
    return verify_bytes(public, manifest.read_bytes(), sig_path.read_bytes())
