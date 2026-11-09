"""The repo itself must stay consistent: every manifest pack has a folder, every
folder has pipeline metadata, and nothing secret is committed.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from holdfast import manifest as mf
from holdfast import util

ROOT = util.repo_root()
PACK_IDS = [p["id"] for p in mf.packs(mf.load())]


def test_the_repo_layout_the_spec_asks_for_exists():
    assert (ROOT / "manifest.json").exists()
    assert (ROOT / "schema" / "manifest.schema.json").exists()
    assert (ROOT / "README.md").exists()
    assert (ROOT / "scripts" / "requirements.txt").exists()
    for workflow in ("update.yml", "validate.yml", "publish.yml"):
        assert (ROOT / ".github" / "workflows" / workflow).exists(), workflow


@pytest.mark.parametrize("pack_id", PACK_IDS)
def test_every_pack_has_a_folder_a_readme_and_metadata(pack_id):
    folder = ROOT / "packs" / pack_id
    assert folder.is_dir()
    assert (folder / "README.md").exists()
    meta = mf.load_pack_meta(pack_id)
    assert meta is not None
    assert meta.id == pack_id
    assert meta.hosting in ("hosted", "linked")


@pytest.mark.parametrize("pack_id", PACK_IDS)
def test_every_pack_meta_declares_a_known_upstream_kind(pack_id):
    meta = mf.load_pack_meta(pack_id)
    assert meta is not None
    assert (meta.upstream or {}).get("kind") in ("kiwix", "geofabrik", "protomaps", "pdfs", "manual", "none")


def test_no_folder_under_packs_is_missing_from_the_manifest():
    folders = {p.name for p in (ROOT / "packs").iterdir() if p.is_dir()}
    assert folders == set(PACK_IDS)


def test_linked_packs_point_at_a_real_upstream_host():
    for pack_id in PACK_IDS:
        meta = mf.load_pack_meta(pack_id)
        entry = mf.require(mf.load(), pack_id)
        if meta and meta.linked and not mf.is_placeholder_url(entry["url"]):
            assert entry["url"].startswith(("https://download.kiwix.org/", "https://huggingface.co/")), pack_id


def test_hosted_packs_either_have_a_builder_or_say_they_are_a_stub():
    for pack_id in PACK_IDS:
        meta = mf.load_pack_meta(pack_id)
        assert meta is not None
        if meta.hosted:
            assert meta.builder, pack_id
            script = meta.builder.split(" ")[0]
            assert (ROOT / script).exists(), f"{pack_id}: {script} does not exist"


def test_every_sources_json_parses_and_lists_documents():
    for path in (ROOT / "packs").rglob("sources.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("documents"), path
        for doc in data["documents"]:
            assert doc.get("id"), path
            assert str(doc.get("url", "")).startswith("https://"), path
            assert "verified" in doc, f"{path}: {doc.get('id')} must say whether its URL was verified"


def test_no_private_key_is_committed():
    offenders = [
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and ".git" not in p.parts
        and p.suffix in (".key", ".pem")
    ]
    assert offenders == []


def test_no_signature_is_committed():
    """publish.yml makes the signature; a committed one would go stale silently."""
    assert not (ROOT / "manifest.json.sig").exists() or (ROOT / ".gitignore").read_text().count("manifest.json.sig")


def test_the_manifest_is_written_with_the_bytes_the_signature_will_cover():
    raw = (ROOT / "manifest.json").read_bytes()
    assert b"\r\n" not in raw, "CRLF in manifest.json would make the signature machine-dependent"
    assert raw.endswith(b"}\n")
    assert raw.decode("utf-8")  # valid UTF-8
    assert not raw.startswith(b"\xef\xbb\xbf"), "a BOM would be signed too"


def test_gitignore_covers_the_things_that_must_never_be_committed():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for pattern in ("*.hfdb", "*.pmtiles", "private.key", "/.cache/", "manifest.json.sig"):
        assert pattern in text, pattern


def test_requirements_are_all_pinned():
    for name in ("requirements.txt", "requirements-dev.txt"):
        for line in (ROOT / "scripts" / name).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-r "):
                continue
            assert re.match(r"^[A-Za-z0-9_.\-]+==[0-9][^\s]*$", line), f"{name}: '{line}' is not pinned exactly"


def test_workflows_never_sign_outside_publish():
    """Exactly one workflow may read the signing secret, and only it may sign."""
    workflows = ROOT / ".github" / "workflows"
    readers = [
        p.name
        for p in workflows.glob("*.yml")
        if "secrets.HOLDFAST_SIGNING_KEY" in p.read_text(encoding="utf-8")
    ]
    assert readers == ["publish.yml"]

    signers = [
        p.name for p in workflows.glob("*.yml") if "sign_manifest.py" in p.read_text(encoding="utf-8")
    ]
    assert signers == ["publish.yml"]


def test_workflows_pin_third_party_actions_to_a_commit_sha():
    pattern = re.compile(r"uses:\s*([^\s@]+)@([^\s#]+)")
    for path in (ROOT / ".github" / "workflows").glob("*.yml"):
        for action, ref in pattern.findall(path.read_text(encoding="utf-8")):
            if action.startswith("./"):
                continue
            assert re.fullmatch(r"[0-9a-f]{40}", ref), f"{path.name}: {action}@{ref} is not a 40-char commit sha"


def test_every_workflow_declares_least_privilege_permissions():
    for path in (ROOT / ".github" / "workflows").glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        assert "permissions:" in text, path.name
        # A top-level permissions block must come before the first job.
        head = text.split("jobs:", 1)[0]
        assert "permissions:" in head, f"{path.name}: no top-level permissions block"


def test_the_content_licence_question_is_recorded_not_guessed():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "CC BY-SA 4.0" in text
    assert "CC0" in text
    assert "placeholder" in text.lower()


def test_region_files_have_a_sane_bbox():
    for path in Path(ROOT / "packs" / "maps-roads-us-md" / "regions").glob("*.json"):
        region = json.loads(path.read_text(encoding="utf-8"))
        min_lon, min_lat, max_lon, max_lat = region["bbox"]
        assert -180 <= min_lon < max_lon <= 180, path
        assert -90 <= min_lat < max_lat <= 90, path
        assert 0 < region["maxzoom"] <= 16, path
