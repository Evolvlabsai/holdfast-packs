"""The JSON Schema must accept what the app accepts and reject what it cannot.

The real risk is the quiet direction: a field the app's parser would skip,
defaulting silently, while CI calls the manifest fine. So these tests check both
that valid manifests pass and that each specific mistake fails.

The repo's own ``manifest.json`` is validated here too, so a hand edit that
breaks it fails ``pytest`` as well as ``validate_manifest.py``.
"""

from __future__ import annotations

import copy
import json

import jsonschema
import pytest

import validate_manifest
from holdfast import manifest as mf

MINIMAL_PACK = {
    "id": "core",
    "version": "2026.11.09",
    "url": "https://example.invalid/PLACEHOLDER/core.hfdb",
    "sha256": "0" * 64,
    "size": 0,
}

MINIMAL = {
    "schema": 1,
    "published": "2026-11-09T00:00:00Z",
    "packs": [MINIMAL_PACK],
}


@pytest.fixture(scope="module")
def schema():
    return json.loads(mf.schema_path().read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def validator(schema):
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def errors(validator, document):
    return [e.message for e in validator.iter_errors(document)]


def with_pack(**overrides):
    document = copy.deepcopy(MINIMAL)
    document["packs"][0].update(overrides)
    return document


# -- passing cases ---------------------------------------------------------


def test_the_schema_is_itself_valid(schema):
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)


def test_the_minimum_the_app_requires_is_enough(validator):
    """id, version, url, sha256, size -- and nothing else -- must validate,
    because that is exactly what CatalogParser.ParseEntry requires."""
    assert errors(validator, MINIMAL) == []


def test_the_repos_own_manifest_validates(validator):
    assert errors(validator, mf.load()) == []


def test_the_repos_manifest_lists_the_launch_packs():
    ids = [p["id"] for p in mf.packs(mf.load())]
    non_map = [i for i in ids if not i.startswith("maps-")]
    assert non_map == [
        "core",
        "medical",
        "medical-wikimed",
        "water-food",
        "manuals",
        "shelter-repair",
        "wikipedia-top50k",
        "offline-ai-model",
        "offline-ai-embedder",
    ]


def test_every_state_has_roads_topo_and_routing_together():
    ids = [p["id"] for p in mf.packs(mf.load()) if p["id"].startswith("maps-")]
    regions = sorted({i.rsplit("-us-", 1)[1] for i in ids})
    assert "md" in regions
    for r in regions:
        group = [i for i in ids if i.endswith("-us-" + r)]
        assert group == [f"maps-roads-us-{r}", f"maps-topo-us-{r}", f"maps-routing-us-{r}"], r


def test_a_fully_populated_pack_validates(validator):
    document = with_pack(
        name="Maryland — roads",
        group="maps",
        region="US-MD",
        published="2026-11-01",
        format="pmtiles",
        size=325058560,
        sha256="a" * 64,
        url="https://github.com/org/repo/releases/download/maps-2026.11/us-md-roads.pmtiles",
        mirrors=["https://bucket.example.com/us-md-roads.pmtiles"],
        delta={
            "from": "2026.10.01",
            "url": "https://example.com/d.patch",
            "sha256": "b" * 64,
            "size": 18350080,
        },
        parts=[
            {"index": 0, "url": "https://example.com/p0", "size": 1, "sha256": "c" * 64},
            {"index": 1, "url": "https://example.com/p1", "size": 2, "sha256": "d" * 64},
        ],
        required=True,
        staleAfterDays=90,
        license="ODbL-1.0",
        attribution="© OpenStreetMap contributors",
        changes="Latest OSM data.",
        minAppVersion="1.0.0",
        description="Streets, trails, points of interest",
    )
    assert errors(validator, document) == []


def test_region_may_be_null(validator):
    assert errors(validator, with_pack(region=None)) == []


def test_the_example_from_the_spec_validates(validator):
    """The Manifest schema block in the spec, verbatim apart from the sha256."""
    spec_example = {
        "schema": 1,
        "published": "2026-11-08T00:00:00Z",
        "minAppVersion": "1.0.0",
        "packs": [
            {
                "id": "maps-roads-us-md",
                "name": "Maryland: roads",
                "group": "maps",
                "region": "US-MD",
                "version": "2026.11.01",
                "published": "2026-11-01",
                "format": "pmtiles",
                "size": 325058560,
                "sha256": "e" * 64,
                "url": "https://github.com/org/repo/releases/download/maps-2026.11/us-md-roads.pmtiles",
                "mirrors": ["https://bucket.example.com/us-md-roads.pmtiles"],
                "delta": {
                    "from": "2026.10.01",
                    "url": "https://example.com/delta",
                    "sha256": "f" * 64,
                    "size": 18350080,
                },
                "required": False,
                "staleAfterDays": 90,
                "license": "ODbL-1.0",
                "attribution": "© OpenStreetMap contributors",
                "changes": "Latest OSM data: new roads, closures, points of interest",
                "minAppVersion": "1.0.0",
            }
        ],
    }
    assert errors(validator, spec_example) == []


# -- failing cases ---------------------------------------------------------


@pytest.mark.parametrize("field", ["schema", "published", "packs"])
def test_a_missing_root_field_fails(validator, field):
    document = copy.deepcopy(MINIMAL)
    del document[field]
    assert errors(validator, document)


@pytest.mark.parametrize("field", ["id", "version", "url", "sha256", "size"])
def test_a_missing_required_pack_field_fails(validator, field):
    document = copy.deepcopy(MINIMAL)
    del document["packs"][0][field]
    assert any(field in message for message in errors(validator, document))


def test_a_misspelled_field_fails(validator):
    """The app would skip 'requried' and default required to false. CI must not."""
    assert errors(validator, with_pack(requried=True))


def test_snake_case_instead_of_camel_case_fails(validator):
    assert errors(validator, with_pack(stale_after_days=30))


def test_a_wrong_schema_number_fails(validator):
    document = copy.deepcopy(MINIMAL)
    document["schema"] = 2
    assert errors(validator, document)


def test_an_uppercase_sha256_fails(validator):
    """CatalogParser lower-cases it, so an upper-case value would still work on
    the phone -- but then the manifest and our own tooling disagree."""
    assert errors(validator, with_pack(sha256="A" * 64))


@pytest.mark.parametrize("value", ["", "abc", "g" * 64, "0" * 63, "0" * 65])
def test_a_malformed_sha256_fails(validator, value):
    assert errors(validator, with_pack(sha256=value))


@pytest.mark.parametrize("value", ["2026-11-09", "2026.11", "26.11.09", "2026.11.09-rc1"])
def test_a_version_that_is_not_yyyy_mm_dd_fails(validator, value):
    assert errors(validator, with_pack(version=value))


def test_a_published_timestamp_without_the_z_fails(validator):
    document = copy.deepcopy(MINIMAL)
    document["published"] = "2026-11-09T00:00:00+00:00"
    assert errors(validator, document)


def test_a_pack_published_with_a_time_fails(validator):
    """The app parses pack dates with an exact yyyy-MM-dd format first."""
    assert errors(validator, with_pack(published="2026-11-09T00:00:00Z"))


def test_an_http_url_fails(validator):
    assert errors(validator, with_pack(url="http://example.com/core.hfdb"))


def test_an_unknown_format_fails(validator):
    assert errors(validator, with_pack(format="sqlite"))


def test_an_unknown_group_fails(validator):
    assert errors(validator, with_pack(group="misc"))


def test_a_negative_size_fails(validator):
    assert errors(validator, with_pack(size=-1))


def test_a_non_integer_size_fails(validator):
    assert errors(validator, with_pack(size="325058560"))


@pytest.mark.parametrize("value", ["Core", "core_pack", "core pack", "-core", "core-", "c"])
def test_a_bad_pack_id_fails(validator, value):
    assert errors(validator, with_pack(id=value))


def test_an_empty_pack_list_fails(validator):
    document = copy.deepcopy(MINIMAL)
    document["packs"] = []
    assert errors(validator, document)


def test_a_min_app_version_that_is_not_semver_fails(validator):
    assert errors(validator, with_pack(minAppVersion="1.0"))


def test_duplicate_mirrors_fail(validator):
    assert errors(validator, with_pack(mirrors=["https://a.example/x", "https://a.example/x"]))


def test_a_delta_missing_its_checksum_fails(validator):
    assert errors(validator, with_pack(delta={"from": "2026.10.01", "url": "https://a.example/d", "size": 1}))


# -- validate_manifest.py end to end ---------------------------------------


def write(tmp_path, document):
    path = tmp_path / "manifest.json"
    path.write_bytes((json.dumps(document, indent=2) + "\n").encode("utf-8"))
    return path


def test_validator_accepts_the_repo_manifest_with_placeholders_allowed(capsys):
    code = validate_manifest.main(["--allow-placeholders", "--no-drift"])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "manifest OK" in out


PLACEHOLDER_PACK = dict(
    id="medical",
    size=0,
    sha256="0" * 64,
    url="https://example.invalid/PLACEHOLDER/medical.hfdb",
)


def test_validator_fails_on_placeholders_by_default(tmp_path, capsys):
    path = write(tmp_path, with_pack(**PLACEHOLDER_PACK))
    code = validate_manifest.main(["--manifest", str(path), "--no-drift"])
    out = capsys.readouterr().out
    assert code == 1
    assert "not publishable yet" in out
    # Every placeholder pack must be named, not just counted.
    assert "medical" in out


def test_validator_names_the_placeholder_sha256_and_size(tmp_path, capsys):
    path = write(tmp_path, with_pack(**PLACEHOLDER_PACK))
    validate_manifest.main(["--manifest", str(path), "--no-drift"])
    out = capsys.readouterr().out
    assert "sha256 is a placeholder" in out
    assert "size is a placeholder" in out
    assert "url is a placeholder" in out


def test_the_repos_manifest_has_no_placeholders_left(capsys):
    assert validate_manifest.main(["--no-drift"]) == 0


def test_validator_rejects_a_schema_violation(tmp_path, capsys):
    path = write(tmp_path, with_pack(format="sqlite"))
    code = validate_manifest.main(["--manifest", str(path), "--allow-placeholders", "--no-drift"])
    assert code == 1
    assert "schema:" in capsys.readouterr().out


def test_validator_requires_exactly_one_required_pack(tmp_path, capsys):
    document = copy.deepcopy(MINIMAL)
    document["packs"][0]["required"] = False
    path = write(tmp_path, document)
    code = validate_manifest.main(["--manifest", str(path), "--allow-placeholders", "--no-drift"])
    assert code == 1
    assert "exactly one pack must be required" in capsys.readouterr().out


def test_validator_rejects_duplicate_ids(tmp_path, capsys):
    document = copy.deepcopy(MINIMAL)
    document["packs"][0]["required"] = True
    document["packs"].append(copy.deepcopy(document["packs"][0]))
    path = write(tmp_path, document)
    code = validate_manifest.main(["--manifest", str(path), "--allow-placeholders", "--no-drift"])
    assert code == 1
    assert "duplicate pack ids" in capsys.readouterr().out


def test_validator_requires_parts_for_a_big_hosted_pack(tmp_path, capsys):
    document = copy.deepcopy(MINIMAL)
    document["packs"][0].update(
        {
            "id": "core",
            "required": True,
            "size": 3 * 1024**3,
            "sha256": "a" * 64,
            "url": "https://github.com/org/repo/releases/download/core-2026.11.09/core.hfdb",
        }
    )
    path = write(tmp_path, document)
    code = validate_manifest.main(["--manifest", str(path), "--no-drift"])
    out = capsys.readouterr().out
    assert code == 1
    assert "over 2 GB" in out


def test_validator_flags_size_drift_over_the_threshold(tmp_path, capsys):
    baseline = copy.deepcopy(MINIMAL)
    baseline["packs"][0].update({"required": True, "size": 100_000_000, "sha256": "a" * 64,
                                 "url": "https://github.com/org/repo/releases/download/x/core.hfdb"})
    current = copy.deepcopy(baseline)
    current["packs"][0]["size"] = 400_000_000

    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_bytes((json.dumps(baseline, indent=2) + "\n").encode("utf-8"))
    path = write(tmp_path, current)

    code = validate_manifest.main(["--manifest", str(path), "--baseline", str(baseline_path)])
    out = capsys.readouterr().out
    assert code == 1
    assert "over the" in out and "threshold" in out


def test_validator_requires_min_app_version_on_a_format_change(tmp_path, capsys):
    baseline = copy.deepcopy(MINIMAL)
    baseline["packs"][0].update({"required": True, "format": "hfdb", "minAppVersion": "0.1.0",
                                 "size": 1000, "sha256": "a" * 64,
                                 "url": "https://github.com/org/repo/releases/download/x/core.hfdb"})
    current = copy.deepcopy(baseline)
    current["packs"][0]["format"] = "pmtiles"

    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_bytes((json.dumps(baseline, indent=2) + "\n").encode("utf-8"))
    path = write(tmp_path, current)

    code = validate_manifest.main(["--manifest", str(path), "--baseline", str(baseline_path)])
    out = capsys.readouterr().out
    assert code == 1
    assert "minAppVersion is still" in out


def test_validator_accepts_a_format_change_with_min_app_version_raised(tmp_path, capsys):
    baseline = copy.deepcopy(MINIMAL)
    baseline["packs"][0].update({"required": True, "format": "hfdb", "minAppVersion": "0.1.0",
                                 "size": 1000, "sha256": "a" * 64,
                                 "url": "https://github.com/org/repo/releases/download/x/core.hfdb"})
    current = copy.deepcopy(baseline)
    current["packs"][0]["format"] = "pmtiles"
    current["packs"][0]["minAppVersion"] = "0.2.0"

    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_bytes((json.dumps(baseline, indent=2) + "\n").encode("utf-8"))
    path = write(tmp_path, current)

    code = validate_manifest.main(["--manifest", str(path), "--baseline", str(baseline_path)])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "minAppVersion raised to 0.2.0" in out


def test_validator_verifies_a_real_file_from_a_dist_directory(tmp_path, capsys):
    from holdfast import hfdb, util

    dist = tmp_path / "dist"
    built = dist / "core.hfdb"
    with hfdb.HfdbWriter(built, "core", "Core", "2026.11.09") as w:
        w.add_document("one", "One", "water and food")
        w.complete()
    size, digest = util.size_and_sha256(built)

    document = copy.deepcopy(MINIMAL)
    document["packs"][0].update(
        {
            "required": True,
            "size": size,
            "sha256": digest,
            "url": "https://github.com/org/repo/releases/download/core-2026.11.09/core.hfdb",
        }
    )
    path = write(tmp_path, document)

    code = validate_manifest.main(["--manifest", str(path), "--dist", str(dist), "--no-drift"])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "matches size and sha256" in out


def test_validator_catches_a_wrong_checksum_in_dist(tmp_path, capsys):
    from holdfast import hfdb, util

    dist = tmp_path / "dist"
    built = dist / "core.hfdb"
    with hfdb.HfdbWriter(built, "core", "Core", "2026.11.09") as w:
        w.add_document("one", "One", "water and food")
        w.complete()
    size, _ = util.size_and_sha256(built)

    document = copy.deepcopy(MINIMAL)
    document["packs"][0].update(
        {
            "required": True,
            "size": size,
            "sha256": "b" * 64,
            "url": "https://github.com/org/repo/releases/download/core-2026.11.09/core.hfdb",
        }
    )
    path = write(tmp_path, document)

    code = validate_manifest.main(["--manifest", str(path), "--dist", str(dist), "--no-drift"])
    out = capsys.readouterr().out
    assert code == 1
    assert "hashes to" in out
