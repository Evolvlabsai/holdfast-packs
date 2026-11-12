"""Build one ``overlays-us-xx`` pack per state: hospitals and designated shelters.

Usage::

    python scripts/build_overlays.py --out dist                 # every state
    python scripts/build_overlays.py --out dist --region us-md  # one state
    python scripts/build_overlays.py --out dist --offline       # use .cache only

Sources (all downloaded into ``.cache/overlays``):

* **Hospitals** -- CMS "Hospital General Information" (data.cms.gov, dataset
  ``xubh-q36u``), public domain, refreshed by CMS every quarter. It carries the
  name, address, phone, hospital type and whether there is an emergency room, but
  no coordinates.
* **Hospital locations** -- ``sources/overlays/hospital-locations.csv`` is a
  committed cache (facility id -> lat/lon/source), so a rebuild only looks up
  hospitals CMS added since. New ones go to the US Census Bureau batch geocoder
  (public domain), then to OpenStreetMap hospitals (ODbL) matched by name near the
  ZIP code, strictly: a wrong hospital location is worse than a missing one.
  ``sources/overlays/hospital-fixes.csv`` overrides both, by hand.
* **Shelters** -- FEMA National Shelter System facilities
  (gis.fema.gov ``NSS/FEMA_NSS`` layer 5), public domain. These are buildings the
  Red Cross or a local agency has designated as shelters. The list does NOT say
  which are open; every pin says so in the app.

What is left out on purpose: shelter contact names, phones and e-mails (people,
not facilities), inactive shelters, and any point outside its state's bounding
box (bad coordinates). Hospitals that could not be placed are written to
``<out>/overlays-unplaced.csv`` for review.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import hfdb, util  # noqa: E402

CMS_DATASET = "https://data.cms.gov/provider-data/api/1/metastore/schemas/dataset/items/xubh-q36u"
NSS_QUERY = "https://gis.fema.gov/arcgis/rest/services/NSS/FEMA_NSS/FeatureServer/5/query"
CENSUS_BATCH = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
CENSUS_BENCHMARKS = ("Public_AR_Current", "Public_AR_Census2020")
OVERPASS = "https://overpass-api.de/api/interpreter"
OVERPASS_QUERY = (
    '[out:json][timeout:600];(area["ISO3166-1"="US"];)->.a;'
    'nwr["amenity"="hospital"](area.a);out center tags;'
)
ZCTA_GAZETTEER = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2024_Gazetteer/2024_Gaz_zcta_national.zip"

# gis.fema.gov and some federal hosts refuse Python's default client name.
USER_AGENT = "curl/8.9.1"

NSS_FIELDS = (
    "shelter_id,shelter_name,address_1,city,state,zip,evacuation_capacity,post_impact_capacity,"
    "ada_compliant,wheelchair_accessible,pet_accommodations_code,generator_onsite,"
    "latitude,longitude,in_100_yr_floodplain,in_500_yr_floodplain,in_surge_slosh_area,"
    "facility_usage_code,shelter_status_code"
)

SHELTER_NOTE = "Designated shelter. It may not be open. Check local radio or news."

# Words that say nothing about which hospital a name means.
GENERIC = {
    "hospital", "hospitals", "medical", "center", "centre", "the", "of", "and", "inc", "llc", "lp",
    "hosp", "ctr", "med", "campus", "a", "at", "dba", "corp", "corporation",
}

# Small words kept lower case when a SHOUTED name is turned into title case.
SMALL = {"of", "and", "the", "at", "for", "in", "on"}
# Brand spellings a plain title case gets wrong.
SPECIAL = {"adventhealth": "AdventHealth", "uchicago": "UChicago", "medstar": "MedStar", "healthpartners": "HealthPartners"}
KEEP_UPPER = {
    "va", "usa", "uc", "ucsf", "ucla", "nyu", "osf", "chi", "ssm", "hca", "ii", "iii", "iv", "llc",
    "inc", "lp", "md", "dc", "ecu", "unc", "ut", "uab", "ohsu", "uams", "upmc", "ymca", "ywca", "ms",
    "jfk", "pc", "cmh", "nw", "ne", "sw", "se",
}


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------


def _open(url: str, data: bytes | None = None, headers: dict[str, str] | None = None, timeout: int = 300):
    h = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    h.update(headers or {})
    return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=h), timeout=timeout)


def _retry(fn, what: str, attempts: int = 4):
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - network: retry anything, then fail loudly
            if attempt == attempts:
                util.fail(f"{what}: {exc}")
            util.warn(f"{what}: {exc} (retry {attempt})")
            time.sleep(5 * attempt)
    return None


def fetch_cms(cache: Path) -> Path:
    dest = cache / "cms-hospitals.csv"
    meta = _retry(lambda: json.load(_open(CMS_DATASET + "?show-reference-ids=false")), "CMS dataset")
    url = next(d["downloadURL"] for d in meta["distribution"] if d.get("downloadURL", "").endswith(".csv"))
    util.info(f"CMS hospitals {meta.get('modified')}: {url}")
    dest.write_bytes(_retry(lambda: _open(url).read(), "CMS download"))
    (cache / "cms-hospitals.modified").write_text(str(meta.get("modified", "")), encoding="utf-8")
    return dest


def fetch_shelters(cache: Path) -> Path:
    dest = cache / "nss-shelters.json"
    rows: list[dict] = []
    offset = 0
    while True:
        query = urllib.parse.urlencode({
            "where": "1=1", "outFields": NSS_FIELDS, "returnGeometry": "false",
            "orderByFields": "objectid", "resultOffset": offset, "resultRecordCount": 4000, "f": "json",
        })
        page = _retry(lambda: json.load(_open(NSS_QUERY + "?" + query)), f"FEMA shelters @{offset}")
        if "error" in page:
            util.fail(f"FEMA shelters: {page['error']}")
        feats = page.get("features") or []
        rows.extend(f["attributes"] for f in feats)
        if not feats or (len(feats) < 4000 and not page.get("exceededTransferLimit")):
            break
        offset += len(feats)
    util.info(f"FEMA shelters: {len(rows)} facilities")
    if len(rows) < 10000:
        util.fail(f"FEMA shelters: only {len(rows)} rows; the service is probably broken. Not building.")
    dest.write_text(json.dumps(rows), encoding="utf-8")
    return dest


# ---------------------------------------------------------------------------
# Hospital locations
# ---------------------------------------------------------------------------


def read_locations(path: Path) -> dict[str, tuple[float, float, str]]:
    out: dict[str, tuple[float, float, str]] = {}
    if path.exists():
        for row in csv.DictReader(path.open(encoding="utf-8")):
            out[row["facility_id"]] = (float(row["lat"]), float(row["lon"]), row["source"])
    return out


def write_locations(path: Path, locs: dict[str, tuple[float, float, str]], names: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["facility_id", "lat", "lon", "source", "name"])
        for fid in sorted(locs):
            lat, lon, src = locs[fid]
            w.writerow([fid, f"{lat:.6f}", f"{lon:.6f}", src, names.get(fid, "")])


def _clean_street(address: str) -> str:
    a = re.split(
        r"\s+-\s+|,|\bP\.?\s?O\.? BOX\b|\bSUITE\b|\bSTE\b|\bBLDG\b|\bBUILDING\b|\bFLOOR\b|\bUNIT\b",
        address.upper(),
    )[0]
    return re.sub(r"\s+", " ", a).strip()


def census_geocode(hospitals: list[dict], cache: Path) -> dict[str, tuple[float, float, str]]:
    found: dict[str, tuple[float, float, str]] = {}
    todo = hospitals
    for clean in (False, True):
        for bench in CENSUS_BENCHMARKS:
            todo = [h for h in todo if h["Facility ID"] not in found]
            if not todo:
                return found
            lines = []
            for h in todo:
                street = _clean_street(h["Address"]) if clean else h["Address"]
                lines.append([h["Facility ID"], street, h["City/Town"], h["State"], h["ZIP Code"][:5]])
            for start in range(0, len(lines), 9000):
                found.update(_census_batch(lines[start:start + 9000], bench))
            util.info(f"Census ({bench}{', cleaned' if clean else ''}): {len(found)} placed so far")
    return found


def _census_batch(lines: list[list[str]], bench: str) -> dict[str, tuple[float, float, str]]:
    import io
    import uuid

    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(lines)
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"benchmark\"\r\n\r\n{bench}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"addressFile\"; filename=\"a.csv\"\r\n"
        f"Content-Type: text/csv\r\n\r\n{buf.getvalue()}\r\n--{boundary}--\r\n"
    ).encode("utf-8")
    text = _retry(
        lambda: _open(CENSUS_BATCH, body, {"Content-Type": f"multipart/form-data; boundary={boundary}"},
                      timeout=1800).read().decode("utf-8", "replace"),
        "Census geocoder",
    )
    out = {}
    for row in csv.reader(text.splitlines()):
        if len(row) > 5 and row[2] == "Match" and "," in row[5]:
            lon, lat = (float(v) for v in row[5].split(","))
            out[row[0]] = (lat, lon, "census")
    return out


def _tokens(name: str) -> set[str]:
    words = re.findall(r"[a-z0-9]+", name.lower().replace("saint", "st"))
    return {w for w in words if w not in GENERIC}


def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def osm_match(hospitals: list[dict], cache: Path) -> dict[str, tuple[float, float, str]]:
    """Name match against OSM hospitals within 20 km of the ZIP centroid. Strict on purpose."""
    import zipfile

    osm_path = cache / "osm-hospitals.json"
    if not osm_path.exists():
        data = urllib.parse.urlencode({"data": OVERPASS_QUERY}).encode()
        osm_path.write_bytes(_retry(
            lambda: _open(OVERPASS, data, {"Accept": "application/json"}, timeout=900).read(), "Overpass"))
    zip_path = cache / "zcta.zip"
    if not zip_path.exists():
        zip_path.write_bytes(_retry(lambda: _open(ZCTA_GAZETTEER).read(), "ZCTA gazetteer"))

    points = []
    for e in json.loads(osm_path.read_text(encoding="utf-8"))["elements"]:
        tags = e.get("tags", {})
        lat = e.get("lat", e.get("center", {}).get("lat"))
        lon = e.get("lon", e.get("center", {}).get("lon"))
        names = [tags[k] for k in ("name", "alt_name", "official_name", "old_name", "short_name") if k in tags]
        if lat is not None and names:
            points.append((lat, lon, [t for t in (_tokens(n) for n in names) if t]))

    zcta: dict[str, tuple[float, float]] = {}
    with zipfile.ZipFile(zip_path) as zf:
        member = next(n for n in zf.namelist() if n.endswith(".txt"))
        for row in csv.reader(zf.read(member).decode("utf-8").splitlines(), delimiter="\t"):
            if row and row[0] != "GEOID":
                zcta[row[0]] = (float(row[5]), float(row[6].strip()))

    found = {}
    for h in hospitals:
        centre = zcta.get(h["ZIP Code"].zfill(5)[:5])
        want = _tokens(h["Facility Name"])
        if not centre or not want:
            continue
        cands = []
        for lat, lon, token_sets in points:
            if abs(lat - centre[0]) > 0.25 or abs(lon - centre[1]) > 0.35:
                continue
            d = _km(centre, (lat, lon))
            if d > 20:
                continue
            best = max(len(want & t) / len(want | t) for t in token_sets)
            if best >= 0.75:
                cands.append((best, d, lat, lon))
        if not cands:
            continue
        cands.sort(key=lambda c: (-c[0], c[1]))
        if len(cands) > 1 and cands[1][0] == cands[0][0] and _km(cands[0][2:], cands[1][2:]) > 1:
            continue  # two equally good hospitals apart: do not guess
        found[h["Facility ID"]] = (cands[0][2], cands[0][3], "osm")
    util.info(f"OpenStreetMap: {len(found)} more placed")
    return found


# ---------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------


def title_case(name: str) -> str:
    """CMS and FEMA names are often SHOUTED. Leave mixed-case names alone."""
    name = re.sub(r"\s+", " ", (name or "").strip())
    if not name or not name.isupper():
        return name
    out = []
    for i, word in enumerate(name.split(" ")):
        lower = word.lower()
        bare = re.sub(r"[^a-z]", "", lower)
        if bare in SPECIAL and lower == bare:
            out.append(SPECIAL[bare])
        elif bare in KEEP_UPPER:
            out.append(word)
        elif i > 0 and lower in SMALL:
            out.append(lower)
        else:
            # Capitalize the first letter and any letter after - / ( . ("Winston-Salem", "St.Mary").
            # Not after an apostrophe, so "MARY'S" becomes "Mary's".
            out.append(re.sub(r"(^|[-/(.])([a-z])", lambda m: m.group(1) + m.group(2).upper(), lower))
    return " ".join(out)


def _point(lat: float, lon: float, props: dict) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [round(lon, 6), round(lat, 6)]},
        "properties": {k: v for k, v in props.items() if v not in (None, "")},
    }


def _yes(value) -> bool | None:
    v = (value or "").strip().upper()
    return True if v == "YES" else False if v == "NO" else None


def hospital_feature(h: dict, loc: tuple[float, float, str]) -> dict:
    kind_text = h["Hospital Type"]
    return _point(loc[0], loc[1], {
        "kind": "medical",
        "name": title_case(h["Facility Name"]),
        "category": "hospital",
        "hospitalType": kind_text,
        "er": h["Emergency Services"].strip().upper() == "YES",
        "address": title_case(h["Address"]),
        "city": title_case(h["City/Town"]),
        "zip": h["ZIP Code"].zfill(5)[:5],
        "phone": _phone(h.get("Telephone Number", "")),
        "source": "CMS",
    })


def _phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw or "")
    return f"({digits[:3]}) {digits[3:6]}-{digits[6:10]}" if len(digits) == 10 else ""


def shelter_feature(s: dict) -> dict:
    caps = [c for c in (s.get("evacuation_capacity"), s.get("post_impact_capacity")) if isinstance(c, int) and c > 0]
    flood = [label for key, label in (("in_100_yr_floodplain", "100-year flood zone"),
                                      ("in_500_yr_floodplain", "500-year flood zone"),
                                      ("in_surge_slosh_area", "storm surge area"))
             if (s.get(key) or "").strip().upper() == "YES"]
    pets_code = (s.get("pet_accommodations_code") or "").strip().upper()
    pets = {"NONE": False, "ONSITE": True, "COHABIT": True}.get(pets_code)
    usage = (s.get("facility_usage_code") or "").strip().upper()
    return _point(s["latitude"], s["longitude"], {
        "kind": "shelter",
        "name": title_case(s.get("shelter_name") or "Shelter"),
        "category": "designated-shelter",
        "use": {"EVAC": "evacuation", "POST": "after the storm", "BOTH": "evacuation and after"}.get(usage),
        "capacity": max(caps) if caps else None,
        "pets": pets,
        "wheelchair": _yes(s.get("wheelchair_accessible")),
        "generator": _yes(s.get("generator_onsite")),
        "flood": ", ".join(flood) or None,
        "address": title_case(s.get("address_1") or ""),
        "city": title_case(s.get("city") or ""),
        "zip": (s.get("zip") or "")[:5],
        "note": SHELTER_NOTE,
        "source": "FEMA NSS",
    })


def region_boxes(root: Path) -> dict[str, dict]:
    boxes = {}
    for path in sorted(root.glob("packs/maps-roads-us-*/regions/us-*.json")):
        r = json.loads(path.read_text(encoding="utf-8"))
        boxes[r["region"]] = r
    return boxes


def inside(box: list[float], lat: float, lon: float, margin: float = 0.25) -> bool:
    return box[0] - margin <= lon <= box[2] + margin and box[1] - margin <= lat <= box[3] + margin


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    root = util.repo_root()
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, help="output directory for overlays-us-xx.hfdb files")
    parser.add_argument("--region", action="append", help="us-md style id; repeat for several (default: all)")
    parser.add_argument("--version", default=None, help="pack version yyyy.MM.dd (default: today, UTC)")
    parser.add_argument("--cache", default=str(root / ".cache" / "overlays"))
    parser.add_argument("--offline", action="store_true", help="use the cached downloads; geocode nothing new")
    args = parser.parse_args(argv)

    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    version = args.version or util.version_today()

    cms_path = cache / "cms-hospitals.csv"
    nss_path = cache / "nss-shelters.json"
    if not args.offline:
        fetch_cms(cache)
        fetch_shelters(cache)
    if not cms_path.exists() or not nss_path.exists():
        util.fail("no cached sources; run without --offline first")

    hospitals = list(csv.DictReader(cms_path.open(encoding="utf-8-sig")))
    shelters = json.loads(nss_path.read_text(encoding="utf-8"))

    loc_path = root / "sources" / "overlays" / "hospital-locations.csv"
    fixes_path = root / "sources" / "overlays" / "hospital-fixes.csv"
    locs = read_locations(loc_path)
    names = {h["Facility ID"]: h["Facility Name"] for h in hospitals}

    new = [h for h in hospitals if h["Facility ID"] not in locs]
    if new and not args.offline:
        util.info(f"{len(new)} hospital(s) without a cached location; looking them up")
        locs.update(census_geocode(new, cache))
        locs.update(osm_match([h for h in new if h["Facility ID"] not in locs], cache))
        write_locations(loc_path, locs, names)
    for fid, (lat, lon, _src) in read_locations(fixes_path).items():
        locs[fid] = (lat, lon, "fix")

    boxes = region_boxes(root)
    wanted = {f"US-{r.split('-')[-1].upper()}" for r in args.region} if args.region else set(boxes)
    unknown = wanted - set(boxes)
    if unknown:
        util.fail(f"no region file for {', '.join(sorted(unknown))}")

    unplaced, dropped_box = [], 0
    by_region: dict[str, dict[str, list]] = {r: {"hospitals": [], "shelters": []} for r in wanted}
    for h in hospitals:
        region = f"US-{h['State'].strip().upper()}"
        if region not in wanted:
            continue
        loc = locs.get(h["Facility ID"])
        if loc is None:
            unplaced.append(h)
            continue
        if not inside(boxes[region]["bbox"], loc[0], loc[1]):
            dropped_box += 1
            unplaced.append(h)
            continue
        by_region[region]["hospitals"].append(hospital_feature(h, loc))

    skipped_shelters = swapped = 0
    for s in shelters:
        region = f"US-{(s.get('state') or '').strip().upper()}"
        if region not in wanted:
            continue
        status = (s.get("shelter_status_code") or "").strip().upper()
        lat, lon = s.get("latitude"), s.get("longitude")
        if status == "INACTIVE" or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            skipped_shelters += 1
            continue
        box = boxes[region]["bbox"]
        if not inside(box, lat, lon):
            # Some states load latitude and longitude the wrong way round (all of Wisconsin did).
            if inside(box, lon, lat):
                s = {**s, "latitude": lon, "longitude": lat}
                swapped += 1
            else:
                skipped_shelters += 1
                continue
        by_region[region]["shelters"].append(shelter_feature(s))

    total_h = total_s = 0
    for region in sorted(wanted):
        code = region.split("-")[1].lower()
        pack_id = f"overlays-us-{code}"
        state = boxes[region]["name"]
        feats = by_region[region]
        feats["hospitals"].sort(key=lambda f: f["properties"]["name"])
        feats["shelters"].sort(key=lambda f: f["properties"]["name"])
        path = out / f"{pack_id}.hfdb"
        with hfdb.HfdbWriter(path, pack_id, f"{state} — hospitals and shelters", version) as writer:
            writer.set_meta("region", region)
            writer.set_meta("built", util.iso_timestamp())
            writer.set_meta("generator", "holdfast-packs/scripts/build_overlays.py")
            for name in ("hospitals", "shelters"):
                if feats[name]:
                    writer.add_overlay(f"us-{code}-{name}", region, json.dumps(
                        {"type": "FeatureCollection", "features": feats[name]},
                        ensure_ascii=False, separators=(",", ":")))
            writer.complete()
        total_h += len(feats["hospitals"])
        total_s += len(feats["shelters"])
        util.info(f"{pack_id}: {len(feats['hospitals'])} hospitals, {len(feats['shelters'])} shelters, "
                  f"{util.human_bytes(path.stat().st_size)}")

    with (out / "overlays-unplaced.csv").open("w", encoding="utf-8", newline="\n") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["facility_id", "name", "address", "city", "state", "zip", "type", "er"])
        for h in sorted(unplaced, key=lambda h: (h["State"], h["Facility Name"])):
            w.writerow([h["Facility ID"], h["Facility Name"], h["Address"], h["City/Town"], h["State"],
                        h["ZIP Code"], h["Hospital Type"], h["Emergency Services"]])

    util.info(f"done: {len(wanted)} pack(s), {total_h} hospitals, {total_s} shelters; "
              f"{len(unplaced)} hospital(s) unplaced ({dropped_box} outside their state), "
              f"{skipped_shelters} shelter(s) skipped, {swapped} with lat/lon swapped back. Unplaced list: {out / 'overlays-unplaced.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
