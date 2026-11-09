"""Sign -> verify round trip, and every way a tampered catalog must fail.

The app's rule is simple and absolute: a manifest with a bad or missing
signature is ignored and the last good one is kept. So the only thing that can
go wrong here is a signature that verifies when it should not.
"""

from __future__ import annotations

import base64
import json

import pytest

import sign_manifest
import verify_manifest
from holdfast import signing

MANIFEST = {
    "schema": 1,
    "published": "2026-11-09T00:00:00Z",
    "minAppVersion": "0.1.0",
    "packs": [
        {
            "id": "core",
            "version": "2026.11.09",
            "url": "https://example.invalid/PLACEHOLDER/core.hfdb",
            "sha256": "0" * 64,
            "size": 0,
        }
    ],
}


@pytest.fixture
def keys():
    private_b64, public_b64 = signing.generate()
    return private_b64, public_b64


@pytest.fixture
def manifest_file(tmp_path):
    path = tmp_path / "manifest.json"
    path.write_bytes((json.dumps(MANIFEST, indent=2) + "\n").encode("utf-8"))
    return path


# -- key handling ----------------------------------------------------------


def test_generate_produces_32_byte_keys(keys):
    private_b64, public_b64 = keys
    assert len(base64.b64decode(private_b64)) == signing.PRIVATE_KEY_LENGTH
    assert len(base64.b64decode(public_b64)) == signing.PUBLIC_KEY_LENGTH


def test_public_key_is_derived_from_the_private_key(keys):
    private_b64, public_b64 = keys
    assert signing.public_base64(signing.load_private(private_b64)) == public_b64


def test_a_key_of_the_wrong_length_is_refused():
    with pytest.raises(signing.SigningError, match="32 bytes"):
        signing.load_private(base64.b64encode(b"short").decode())


def test_a_key_that_is_not_base64_is_refused():
    with pytest.raises(signing.SigningError, match="base64"):
        signing.load_public("this is not base64 !!!")


# -- round trip ------------------------------------------------------------


def test_round_trip(keys, manifest_file):
    private_b64, public_b64 = keys
    private = signing.load_private(private_b64)
    sig_path = signing.sign_file(private, manifest_file)
    assert signing.verify_file(signing.load_public(public_b64), manifest_file)
    # The app accepts base64 text or raw bytes; we write base64 plus a newline.
    text = sig_path.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert len(base64.b64decode(text.strip())) == signing.SIGNATURE_LENGTH


def test_signature_file_is_accepted_as_raw_bytes_too(keys, manifest_file):
    """CatalogVerifier.TryReadSignature accepts the raw 64 bytes as well."""
    private_b64, public_b64 = keys
    private = signing.load_private(private_b64)
    raw = signing.sign_bytes(private, manifest_file.read_bytes())
    assert signing.verify_bytes(signing.load_public(public_b64), manifest_file.read_bytes(), raw)


def test_signature_with_whitespace_still_verifies(keys, manifest_file):
    """The app strips all whitespace before decoding, so wrapping is harmless."""
    private_b64, public_b64 = keys
    private = signing.load_private(private_b64)
    signature = signing.sign_bytes(private, manifest_file.read_bytes())
    wrapped = base64.b64encode(signature).decode()
    noisy = ("  " + wrapped[:20] + "\n" + wrapped[20:] + "\r\n  ").encode()
    assert signing.verify_bytes(signing.load_public(public_b64), manifest_file.read_bytes(), noisy)


# -- tamper detection ------------------------------------------------------


def test_a_changed_byte_breaks_the_signature(keys, manifest_file):
    private_b64, public_b64 = keys
    signing.sign_file(signing.load_private(private_b64), manifest_file)

    tampered = json.loads(manifest_file.read_text(encoding="utf-8"))
    tampered["packs"][0]["url"] = "https://attacker.example/evil.hfdb"
    manifest_file.write_bytes((json.dumps(tampered, indent=2) + "\n").encode("utf-8"))

    assert not signing.verify_file(signing.load_public(public_b64), manifest_file)


def test_reindenting_the_manifest_breaks_the_signature(keys, manifest_file):
    """The signature covers exact bytes, not a canonical form. This is why
    update_manifest.py deletes the .sig and publish.yml re-signs."""
    private_b64, public_b64 = keys
    signing.sign_file(signing.load_private(private_b64), manifest_file)

    same_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    manifest_file.write_bytes((json.dumps(same_data, indent=4) + "\n").encode("utf-8"))

    assert not signing.verify_file(signing.load_public(public_b64), manifest_file)


def test_a_trailing_newline_change_breaks_the_signature(keys, manifest_file):
    private_b64, public_b64 = keys
    signing.sign_file(signing.load_private(private_b64), manifest_file)
    manifest_file.write_bytes(manifest_file.read_bytes() + b"\n")
    assert not signing.verify_file(signing.load_public(public_b64), manifest_file)


def test_another_key_cannot_sign_for_us(manifest_file):
    ours_private, ours_public = signing.generate()
    theirs_private, _ = signing.generate()
    signing.sign_file(signing.load_private(theirs_private), manifest_file)
    assert not signing.verify_file(signing.load_public(ours_public), manifest_file)
    assert signing.verify_file(
        signing.load_public(signing.public_base64(signing.load_private(theirs_private))), manifest_file
    )
    assert ours_private != theirs_private


def test_a_flipped_bit_in_the_signature_fails(keys, manifest_file):
    private_b64, public_b64 = keys
    sig_path = signing.sign_file(signing.load_private(private_b64), manifest_file)
    raw = bytearray(base64.b64decode(sig_path.read_text().strip()))
    raw[0] ^= 0x01
    sig_path.write_text(base64.b64encode(bytes(raw)).decode() + "\n", encoding="utf-8")
    assert not signing.verify_file(signing.load_public(public_b64), manifest_file)


@pytest.mark.parametrize(
    "junk",
    [b"", b"not base64 at all", b"AAAA", b"x" * 600, base64.b64encode(b"short")],
)
def test_a_malformed_signature_file_fails_without_raising(keys, manifest_file, junk):
    _, public_b64 = keys
    assert not signing.verify_bytes(signing.load_public(public_b64), manifest_file.read_bytes(), junk)


def test_a_signature_for_a_different_manifest_fails(keys, tmp_path):
    private_b64, public_b64 = keys
    private = signing.load_private(private_b64)

    first = tmp_path / "a.json"
    second = tmp_path / "b.json"
    first.write_bytes(b'{"schema": 1}\n')
    second.write_bytes(b'{"schema": 2}\n')
    sig = signing.sign_file(private, first)

    assert not signing.verify_bytes(signing.load_public(public_b64), second.read_bytes(), sig.read_bytes())


def test_missing_signature_file_is_an_error_not_a_pass(keys, manifest_file):
    _, public_b64 = keys
    with pytest.raises(signing.SigningError, match="not found"):
        signing.verify_file(signing.load_public(public_b64), manifest_file)


# -- the CLI entry points --------------------------------------------------


def test_cli_sign_then_verify(keys, manifest_file, tmp_path, capsys):
    private_b64, public_b64 = keys
    key_file = tmp_path / "private.key"
    key_file.write_text(private_b64 + "\n", encoding="utf-8")

    assert sign_manifest.main(["--manifest", str(manifest_file), "--key-file", str(key_file)]) == 0
    assert verify_manifest.main(["--manifest", str(manifest_file), "--pub", public_b64]) == 0
    assert "signature OK" in capsys.readouterr().out


def test_cli_verify_reports_a_tampered_manifest(keys, manifest_file, capsys):
    private_b64, public_b64 = keys
    sign_manifest.main(["--manifest", str(manifest_file), "--key", private_b64])
    manifest_file.write_bytes(manifest_file.read_bytes().replace(b'"schema": 1', b'"schema": 9'))

    assert verify_manifest.main(["--manifest", str(manifest_file), "--pub", public_b64]) == 1
    assert "signature INVALID" in capsys.readouterr().out


def test_cli_sign_refuses_an_empty_catalog(keys, tmp_path):
    private_b64, _ = keys
    empty = tmp_path / "manifest.json"
    empty.write_bytes(b'{"schema": 1, "published": "2026-11-09T00:00:00Z", "packs": []}\n')
    with pytest.raises(SystemExit) as exc:
        sign_manifest.main(["--manifest", str(empty), "--key", private_b64])
    assert exc.value.code == 1


def test_cli_sign_refuses_a_manifest_missing_published(keys, tmp_path):
    private_b64, _ = keys
    bad = tmp_path / "manifest.json"
    bad.write_bytes(b'{"schema": 1, "packs": [{"id": "x"}]}\n')
    with pytest.raises(SystemExit):
        sign_manifest.main(["--manifest", str(bad), "--key", private_b64])
    assert not (tmp_path / "manifest.json.sig").exists()
