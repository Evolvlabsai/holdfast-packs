"""build_overlays.py: the pure parts (names, features, boxes) and an offline build."""

from __future__ import annotations

import csv
import json
import sqlite3

import build_overlays as bo


def test_shouted_names_become_title_case():
    assert bo.title_case("SAINT MARY'S HOSPITAL") == "Saint Mary's Hospital"
    assert bo.title_case("WINSTON-SALEM VA MEDICAL CENTER") == "Winston-Salem VA Medical Center"
    assert bo.title_case("UNIVERSITY OF MARYLAND MEDICAL CENTER") == "University of Maryland Medical Center"
    assert bo.title_case("UCHICAGO MEDICINE ADVENTHEALTH LA GRANGE") == "UChicago Medicine AdventHealth La Grange"


def test_mixed_case_names_are_left_alone():
    assert bo.title_case("MedStar Union Memorial") == "MedStar Union Memorial"


def test_phone_numbers_are_formatted_or_dropped():
    assert bo._phone("4105542227") == "(410) 554-2227"
    assert bo._phone("(410) 554-2227") == "(410) 554-2227"
    assert bo._phone("554-2227") == ""


def _cms_row(**over):
    row = {
        "Facility ID": "210001", "Facility Name": "TEST GENERAL HOSPITAL", "Address": "1 MAIN STREET",
        "City/Town": "BALTIMORE", "State": "MD", "ZIP Code": "21201", "Telephone Number": "4105550100",
        "Hospital Type": "Acute Care Hospitals", "Emergency Services": "Yes",
    }
    row.update(over)
    return row


def _nss_row(**over):
    row = {
        "shelter_id": 1, "shelter_name": "TEST MIDDLE SCHOOL", "address_1": "2 SCHOOL ROAD", "city": "BALTIMORE",
        "state": "MD", "zip": "21201", "evacuation_capacity": 300, "post_impact_capacity": 150,
        "ada_compliant": "YES", "wheelchair_accessible": "YES", "pet_accommodations_code": "NONE",
        "generator_onsite": "NO", "latitude": 39.29, "longitude": -76.61, "in_100_yr_floodplain": "NO",
        "in_500_yr_floodplain": "YES", "in_surge_slosh_area": " ", "facility_usage_code": "EVAC",
        "shelter_status_code": "CLOSED",
    }
    row.update(over)
    return row


def test_a_hospital_feature_carries_what_the_card_shows():
    f = bo.hospital_feature(_cms_row(), (39.3, -76.6, "census"))
    p = f["properties"]
    assert f["geometry"]["coordinates"] == [-76.6, 39.3]
    assert p["kind"] == "medical" and p["category"] == "hospital"
    assert p["name"] == "Test General Hospital"
    assert p["er"] is True
    assert p["phone"] == "(410) 555-0100"


def test_a_shelter_feature_says_it_may_not_be_open_and_has_no_contact_people():
    p = bo.shelter_feature(_nss_row())["properties"]
    assert p["kind"] == "shelter"
    assert "may not be open" in p["note"]
    assert p["capacity"] == 300
    assert p["pets"] is False
    assert p["wheelchair"] is True and p["generator"] is False
    assert p["flood"] == "500-year flood zone"
    assert not any(k.startswith("org_") or "poc" in k or "email" in k for k in p)


def test_unknown_values_are_left_out_not_guessed():
    p = bo.shelter_feature(_nss_row(pet_accommodations_code=" ", generator_onsite=None,
                                    evacuation_capacity=None, post_impact_capacity=0))["properties"]
    assert "pets" not in p and "generator" not in p and "capacity" not in p


def test_boxes_have_a_margin():
    box = [-79.49, 37.88, -75.05, 39.73]
    assert bo.inside(box, 39.0, -76.5)
    assert bo.inside(box, 39.8, -76.5)  # within the 0.25 degree margin
    assert not bo.inside(box, 43.1, -88.3)


def test_offline_build_writes_one_pack_per_state(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    cache.mkdir()
    with (cache / "cms-hospitals.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(_cms_row()))
        w.writeheader()
        w.writerow(_cms_row())
        w.writerow(_cms_row(**{"Facility ID": "210002", "Facility Name": "NOWHERE HOSPITAL"}))
    shelters = [
        _nss_row(),
        _nss_row(shelter_id=2, shelter_name="SWAPPED", latitude=-76.6, longitude=39.3),
        _nss_row(shelter_id=3, shelter_name="GONE", shelter_status_code="INACTIVE"),
        _nss_row(shelter_id=4, shelter_name="NO PLACE", latitude=None),
    ]
    (cache / "nss-shelters.json").write_text(json.dumps(shelters), encoding="utf-8")

    root = tmp_path / "repo"
    region = root / "packs" / "maps-roads-us-md" / "regions"
    region.mkdir(parents=True)
    (region / "us-md.json").write_text(json.dumps(
        {"id": "us-md", "name": "Maryland", "region": "US-MD", "bbox": [-79.49, 37.88, -75.05, 39.73]}),
        encoding="utf-8")
    (root / "sources" / "overlays").mkdir(parents=True)
    (root / "sources" / "overlays" / "hospital-locations.csv").write_text(
        "facility_id,lat,lon,source,name\n210001,39.300000,-76.600000,census,TEST GENERAL HOSPITAL\n",
        encoding="utf-8")
    monkeypatch.setattr(bo.util, "repo_root", lambda: root)

    out = tmp_path / "dist"
    assert bo.main(["--out", str(out), "--cache", str(cache), "--offline", "--version", "2026.11.11"]) == 0

    cn = sqlite3.connect(f"file:{(out / 'overlays-us-md.hfdb').as_posix()}?mode=ro", uri=True)
    try:
        rows = dict(cn.execute("select overlay_id, geojson from overlays").fetchall())
        meta = dict(cn.execute("select key, value from meta").fetchall())
    finally:
        cn.close()
    assert meta["id"] == "overlays-us-md" and meta["region"] == "US-MD"
    hospitals = json.loads(rows["us-md-hospitals"])["features"]
    shelters = json.loads(rows["us-md-shelters"])["features"]
    assert [h["properties"]["name"] for h in hospitals] == ["Test General Hospital"]
    assert sorted(s["properties"]["name"] for s in shelters) == ["Swapped", "Test Middle School"]
    swapped = next(s for s in shelters if s["properties"]["name"] == "Swapped")
    assert swapped["geometry"]["coordinates"] == [-76.6, 39.3]

    unplaced = list(csv.DictReader((out / "overlays-unplaced.csv").open(encoding="utf-8")))
    assert [u["facility_id"] for u in unplaced] == ["210002"]
