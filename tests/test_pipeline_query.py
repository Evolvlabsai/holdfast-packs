"""The questions the workflows ask must be answerable outside a workflow.

These exist because the alternative — inline `python -c` in an indented `run:`
block — fails with an IndentationError that nothing catches until the cron job
runs at 07:00 on a Monday.
"""

from __future__ import annotations

import base64
import json
import re

import pytest

import pipeline_query
from holdfast import manifest as mf
from holdfast import signing


def test_pack_ids_lists_every_pack(capsys):
    assert pipeline_query.main(["pack-ids"]) == 0
    ids = capsys.readouterr().out.strip().split(",")
    assert sorted(ids) == sorted(p["id"] for p in mf.packs(mf.load()))


@pytest.mark.parametrize(
    ("pack_id", "field", "expected"),
    [
        ("core", "hosting", "hosted"),
        ("core", "upstream.kind", "none"),
        ("shelter-repair", "hosting", "linked"),
        ("shelter-repair", "upstream.book", "ifixit_en_all"),
        ("wikipedia-top50k", "upstream.flavour", "maxi"),
        ("maps-routing-us-md", "upstream.path", "north-america/us/maryland"),
    ],
)
def test_meta_reads_nested_fields(capsys, pack_id, field, expected):
    assert pipeline_query.main(["meta", "--id", pack_id, "--field", field]) == 0
    assert capsys.readouterr().out.strip() == expected


def test_meta_returns_the_default_for_a_missing_field(capsys):
    assert pipeline_query.main(["meta", "--id", "core", "--field", "nope.nope", "--default", "hosted"]) == 0
    assert capsys.readouterr().out.strip() == "hosted"


def test_meta_fails_for_an_unknown_pack():
    with pytest.raises(SystemExit):
        pipeline_query.main(["meta", "--id", "not-a-pack", "--field", "hosting"])


def test_upstream_url_reads_a_check_report(tmp_path, capsys):
    report = tmp_path / "upstream.json"
    report.write_text(
        json.dumps(
            {
                "checks": [
                    {"pack_id": "core", "state": "unchanged"},
                    {"pack_id": "shelter-repair", "url": "https://download.kiwix.org/zim/ifixit/x.zim"},
                ]
            }
        ),
        encoding="utf-8",
    )
    assert pipeline_query.main(["upstream-url", "--id", "shelter-repair", "--report", str(report)]) == 0
    assert capsys.readouterr().out.strip() == "https://download.kiwix.org/zim/ifixit/x.zim"


def test_upstream_url_is_empty_when_nothing_resolved(tmp_path, capsys):
    report = tmp_path / "upstream.json"
    report.write_text(json.dumps({"checks": [{"pack_id": "core"}]}), encoding="utf-8")
    assert pipeline_query.main(["upstream-url", "--id", "core", "--report", str(report)]) == 0
    assert capsys.readouterr().out.strip() == ""


def test_upstream_url_is_empty_when_there_is_no_report(tmp_path, capsys):
    assert pipeline_query.main(["upstream-url", "--id", "core", "--report", str(tmp_path / "none.json")]) == 0
    assert capsys.readouterr().out.strip() == ""


def test_public_key_derives_from_the_secret(monkeypatch, capsys):
    private_b64, public_b64 = signing.generate()
    monkeypatch.setenv("TEST_SIGNING_KEY", private_b64)
    assert pipeline_query.main(["public-key", "--env", "TEST_SIGNING_KEY"]) == 0
    printed = capsys.readouterr().out.strip()
    assert printed == public_b64
    assert len(base64.b64decode(printed)) == 32
    assert private_b64 not in printed


def test_public_key_fails_without_the_secret(monkeypatch):
    monkeypatch.delenv("TEST_SIGNING_KEY", raising=False)
    with pytest.raises(SystemExit):
        pipeline_query.main(["public-key", "--env", "TEST_SIGNING_KEY"])


def test_public_key_fails_on_a_junk_secret(monkeypatch):
    monkeypatch.setenv("TEST_SIGNING_KEY", "not a key")
    with pytest.raises(SystemExit):
        pipeline_query.main(["public-key", "--env", "TEST_SIGNING_KEY"])


def test_manifest_bytes_accepts_the_repo_manifest(capsys):
    assert pipeline_query.main(["manifest-bytes"]) == 0
    assert "LF, no BOM" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (b'{\r\n  "a": 1\r\n}\n', "CRLF"),
        (b'\xef\xbb\xbf{\n  "a": 1\n}\n', "BOM"),
        (b'{\n  "a": 1\n}', "exactly one newline"),
        (b'{\n  "a": 1\n}\n\n', "exactly one newline"),
    ],
)
def test_manifest_bytes_rejects_unsignable_bytes(tmp_path, capsys, raw, expected):
    path = tmp_path / "manifest.json"
    path.write_bytes(raw)
    assert pipeline_query.main(["manifest-bytes", "--manifest", str(path)]) == 1
    assert expected in capsys.readouterr().err


def test_no_workflow_embeds_a_multiline_python_program():
    """An indented `python -c "` with a newline inside is an IndentationError
    waiting for a cron run. All of it lives in pipeline_query.py instead."""
    from holdfast import util

    for path in (util.repo_root() / ".github" / "workflows").glob("*.yml"):
        text = path.read_text(encoding="utf-8")
        assert not re.search(r"""python -c ["'][^"']*\n""", text), f"{path.name} embeds a multi-line python -c"
        assert "python - <<" not in text, f"{path.name} embeds a python heredoc"
