"""update_manifest.py must change exactly what it was asked to and nothing else.

It is the only thing that writes size and sha256 into the manifest, so the tests
that matter are the refusals: a version that does not sort higher, a format
change without a minAppVersion bump, and a stale signature left in place.
"""

from __future__ import annotations

import copy
import json

import pytest

import update_manifest
from holdfast import hfdb, util
from holdfast import manifest as mf

BASE = {
    "schema": 1,
    "published": "2026-11-01T00:00:00Z",
    "minAppVersion": "0.1.0",
    "packs": [
        {
            "id": "core",
            "name": "Core",
            "group": "essentials",
            "version": "2026.11.01",
            "published": "2026-11-01",
            "format": "hfdb",
            "size": 0,
            "sha256": "0" * 64,
            "url": "https://example.invalid/PLACEHOLDER/core.hfdb",
            "mirrors": [],
            "required": True,
            "staleAfterDays": 7,
            "license": "x",
            "attribution": "y",
            "changes": "Not built yet.",
            "minAppVersion": "0.1.0",
        },
        {
            "id": "shelter-repair",
            "version": "2025.12.23",
            "format": "zim",
            "size": 3570695757,
            "sha256": "9bb5f3408707fd0300c6ef47a425c3217187f144cd9154a928183816aa72eead",
            "url": "https://download.kiwix.org/zim/ifixit/ifixit_en_all_2025-12.zim",
        },
    ],
}


@pytest.fixture
def manifest_file(tmp_path):
    path = tmp_path / "manifest.json"
    util.write_json(path, copy.deepcopy(BASE))
    return path


@pytest.fixture
def built_pack(tmp_path):
    path = tmp_path / "dist" / "core.hfdb"
    with hfdb.HfdbWriter(path, "core", "Core", "2026.11.09") as w:
        w.add_document("kit", "Build an emergency kit", "One gallon of water per person per day.")
        w.complete()
    return path


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


# -- the happy path --------------------------------------------------------


def test_a_rebuilt_hosted_pack_gets_real_size_and_sha256(manifest_file, built_pack):
    url = "https://github.com/org/repo/releases/download/core-2026.11.09/core.hfdb"
    code = update_manifest.main(
        [
            "--id", "core",
            "--manifest", str(manifest_file),
            "--file", str(built_pack),
            "--url", url,
            "--version", "2026.11.09",
            "--published", "2026-11-09",
            "--changes", "Shelter list refreshed.",
        ]
    )
    assert code == 0

    size, digest = util.size_and_sha256(built_pack)
    entry = mf.require(read(manifest_file), "core")
    assert entry["size"] == size
    assert entry["sha256"] == digest
    assert entry["url"] == url
    assert entry["version"] == "2026.11.09"
    assert entry["published"] == "2026-11-09"
    assert entry["changes"] == "Shelter list refreshed."
    assert mf.placeholder_reasons(entry) == []


def test_the_root_published_timestamp_moves(manifest_file, built_pack):
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb", "--version", "2026.11.09"]
    )
    assert read(manifest_file)["published"] != BASE["published"]
    assert read(manifest_file)["published"].endswith("Z")


def test_other_packs_are_untouched(manifest_file, built_pack):
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb", "--version", "2026.11.09"]
    )
    assert mf.require(read(manifest_file), "shelter-repair") == BASE["packs"][1]


def test_pack_order_is_preserved(manifest_file, built_pack):
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb", "--version", "2026.11.09"]
    )
    assert [p["id"] for p in mf.packs(read(manifest_file))] == ["core", "shelter-repair"]


def test_fields_come_out_in_the_apps_own_order(manifest_file, built_pack):
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb", "--version", "2026.11.09"]
    )
    keys = list(mf.require(read(manifest_file), "core").keys())
    expected = [k for k in update_manifest.FIELD_ORDER if k in keys]
    assert keys == expected


def test_mirrors_can_be_replaced(manifest_file, built_pack):
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb", "--version", "2026.11.09",
         "--mirror", "https://r2.example.com/core.hfdb", "--mirror", "https://b.example.com/core.hfdb"]
    )
    assert mf.require(read(manifest_file), "core")["mirrors"] == [
        "https://r2.example.com/core.hfdb",
        "https://b.example.com/core.hfdb",
    ]


def test_explicit_size_and_sha256_are_accepted(manifest_file):
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--version", "2026.11.09",
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb",
         "--size", "12345", "--sha256", "A" * 64]
    )
    entry = mf.require(read(manifest_file), "core")
    assert entry["size"] == 12345
    assert entry["sha256"] == "a" * 64  # lower-cased, as the app expects


def test_dry_run_writes_nothing(manifest_file, built_pack):
    before = manifest_file.read_bytes()
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb", "--version", "2026.11.09",
         "--dry-run"]
    )
    assert manifest_file.read_bytes() == before


def test_the_byte_layout_round_trips(manifest_file, built_pack):
    """Two-space indent, LF, one trailing newline -- the bytes the signature covers."""
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb", "--version", "2026.11.09"]
    )
    raw = manifest_file.read_bytes()
    assert b"\r\n" not in raw
    assert raw.endswith(b"}\n")
    assert raw.count(b"\n}\n") == 1
    assert b'\n  "schema": 1,' in raw


# -- refusals --------------------------------------------------------------


def test_a_version_that_does_not_sort_higher_is_refused(manifest_file, built_pack):
    with pytest.raises(SystemExit) as exc:
        update_manifest.main(
            ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
             "--version", "2026.10.01"]
        )
    assert exc.value.code == 1
    assert read(manifest_file) == BASE


def test_the_same_version_is_refused_without_the_flag(manifest_file, built_pack):
    with pytest.raises(SystemExit):
        update_manifest.main(
            ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
             "--version", "2026.11.01"]
        )


def test_the_same_version_is_allowed_with_the_flag(manifest_file, built_pack):
    code = update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--version", "2026.11.01", "--allow-same-version"]
    )
    assert code == 0
    assert mf.require(read(manifest_file), "core")["version"] == "2026.11.01"


def test_an_unknown_pack_id_is_refused(manifest_file):
    with pytest.raises(SystemExit):
        update_manifest.main(["--id", "nope", "--manifest", str(manifest_file), "--version", "2026.11.09"])


def test_a_missing_build_file_is_refused(manifest_file, tmp_path):
    with pytest.raises(SystemExit):
        update_manifest.main(
            ["--id", "core", "--manifest", str(manifest_file), "--file", str(tmp_path / "nope.hfdb"),
             "--version", "2026.11.09"]
        )


def test_a_format_change_without_min_app_version_is_refused(manifest_file, built_pack):
    with pytest.raises(SystemExit):
        update_manifest.main(
            ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
             "--version", "2026.11.09", "--format", "pmtiles"]
        )
    assert mf.require(read(manifest_file), "core")["format"] == "hfdb"


def test_a_format_change_with_min_app_version_is_allowed(manifest_file, built_pack):
    code = update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--version", "2026.11.09", "--format", "pmtiles", "--min-app-version", "0.2.0"]
    )
    assert code == 0
    entry = mf.require(read(manifest_file), "core")
    assert entry["format"] == "pmtiles"
    assert entry["minAppVersion"] == "0.2.0"


def test_an_unknown_format_is_refused(manifest_file, built_pack):
    with pytest.raises(SystemExit):
        update_manifest.main(
            ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
             "--version", "2026.11.09", "--format", "graph", "--min-app-version", "0.2.0"]
        )


def test_a_stale_signature_is_deleted(manifest_file, built_pack):
    sig = manifest_file.with_name("manifest.json.sig")
    sig.write_text("not a real signature\n", encoding="utf-8")
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb", "--version", "2026.11.09"]
    )
    assert not sig.exists()


def test_an_entry_that_is_still_a_placeholder_says_so(manifest_file, built_pack, capsys):
    """Measuring the file but leaving the url a placeholder must not look clean."""
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack), "--version", "2026.11.09"]
    )
    assert "STILL a placeholder" in capsys.readouterr().out


def test_record_upstream_warns_when_there_is_no_pack_meta(manifest_file, built_pack, capsys, monkeypatch, tmp_path):
    monkeypatch.setattr(util, "repo_root", lambda: tmp_path)
    monkeypatch.setattr(mf.util, "repo_root", lambda: tmp_path)
    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb",
         "--version", "2026.11.09", "--record-upstream", "whatever"]
    )
    assert "had nothing to update" in capsys.readouterr().err


def test_record_upstream_updates_pack_meta(manifest_file, built_pack, tmp_path, monkeypatch):
    pack_dir = tmp_path / "packs" / "core"
    pack_dir.mkdir(parents=True)
    util.write_json(pack_dir / "pack.meta.json", {"id": "core", "upstream": {"kind": "kiwix", "book": "b"}})
    monkeypatch.setattr(mf.util, "repo_root", lambda: tmp_path)

    update_manifest.main(
        ["--id", "core", "--manifest", str(manifest_file), "--file", str(built_pack),
         "--url", "https://github.com/org/repo/releases/download/x/core.hfdb",
         "--version", "2026.11.09", "--record-upstream", "book_2026-11.zim"]
    )
    meta = json.loads((pack_dir / "pack.meta.json").read_text(encoding="utf-8"))
    assert meta["upstream"]["currentFile"] == "book_2026-11.zim"
