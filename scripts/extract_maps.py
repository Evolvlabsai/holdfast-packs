#!/usr/bin/env python3
"""Cut a per-state road basemap out of the Protomaps daily planet build.

    python scripts/extract_maps.py --region us-md --out dist/us-md-roads.pmtiles
    python scripts/extract_maps.py --region us-md --dry-run     # cost estimate, no download

Wraps the ``pmtiles`` CLI from protomaps/go-pmtiles. ``pmtiles extract`` reads
the remote archive over HTTP range requests and writes a small local archive, so
a state costs a few hundred MB of transfer instead of the ~130 GB planet.

    pmtiles extract <planet url> <out> --bbox=minlon,minlat,maxlon,maxlat --maxzoom=14

Regions live in ``packs/maps-roads-us-md/regions/*.json``: id, name, bbox,
maxzoom, licence and attribution. Adding a state is a new file there plus a new
manifest entry -- see "How to add a state" in README.md.

----------------------------------------------------------------------------
HOSTING NOTE -- this contradicts the spec, on purpose.

The spec's pack table calls "Maps: roads (per state)" **Linked**, hosted by
"OpenStreetMap via Geofabrik or Protomaps". Neither of them publishes a
per-state PMTiles file:

* Protomaps publishes one daily **planet** archive (~130 GB). A phone cannot
  stream it offline, and the app's one-URL-per-pack contract has no way to
  express "range-read this slice".
* Geofabrik publishes per-state ``.osm.pbf`` **data**, not tiles. Turning that
  into tiles is a build step (planetiler or tilemaker), not a link.

So the extract this script produces has to be **hosted by us** on GitHub
Releases, exactly like topo and routing: roads is a Hosted pack, not a Linked
one, and ``packs/maps-roads-us-md/pack.meta.json`` says ``"hosting": "hosted"``.
That is ~310 MB per state of our release storage and bandwidth. It stays free
(releases are free and unmetered for public repos within the acceptable-use
policy) but it is not the $0-and-no-storage the spec's "Linked" implies. If a
popular state starts drawing real traffic, the mirror field moves it to R2.

Attribution duty comes with it: ODbL requires the OpenStreetMap credit to be
shown on the map, which the manifest's ``attribution`` field carries.
----------------------------------------------------------------------------
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import httpcache, util  # noqa: E402

#: Daily planet basemap. Confirmed pattern: one archive per UTC build date.
PLANET_URL = "https://build.protomaps.com/{date}.pmtiles"

#: Machine-readable index of the published builds (key, size, uploaded, version).
BUILDS_INDEX = "https://build-metadata.protomaps.dev/builds.json"

PMTILES_HINT = (
    "Install the go-pmtiles CLI: download the asset for your platform from "
    "https://github.com/protomaps/go-pmtiles/releases (e.g. "
    "go-pmtiles_1.31.2_Linux_x86_64.tar.gz), unpack it and put `pmtiles` on PATH. "
    "In CI, see .github/workflows/update.yml."
)


def regions_dir(root: Path) -> Path:
    return root / "packs" / "maps-roads-us-md" / "regions"


def load_region(root: Path, region_id: str) -> dict:
    path = regions_dir(root) / f"{region_id}.json"
    if not path.exists():
        available = ", ".join(sorted(p.stem for p in regions_dir(root).glob("*.json"))) or "none"
        util.fail(f"no region file {path} (available: {available})")
    region = json.loads(path.read_text(encoding="utf-8"))
    for field in ("id", "bbox"):
        if field not in region:
            util.fail(f"{path}: missing '{field}'")
    bbox = region["bbox"]
    if not (isinstance(bbox, list) and len(bbox) == 4):
        util.fail(f"{path}: bbox must be [min_lon, min_lat, max_lon, max_lat]")
    return region


def latest_build_date() -> str:
    """Newest published planet build, from the builds index.

    The bucket root has no listing and there is no ``latest.pmtiles`` alias, so
    this index is the only way to resolve "newest".
    """
    try:
        raw = httpcache.get_text(BUILDS_INDEX)
        builds = json.loads(raw)
    except Exception as exc:  # noqa: BLE001 - network or shape, same remedy
        util.fail(f"could not read {BUILDS_INDEX} ({exc}). Pass --planet-date YYYYMMDD to pin a build.")

    dates = sorted(
        {
            str(b.get("key", "")).removesuffix(".pmtiles")
            for b in builds
            if str(b.get("key", "")).endswith(".pmtiles") and str(b.get("key", ""))[:8].isdigit()
        }
    )
    if not dates:
        util.fail(f"{BUILDS_INDEX} listed no .pmtiles builds. Pass --planet-date YYYYMMDD.")
    return dates[-1][:8]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--region", required=True, help="region id, e.g. us-md (packs/maps-roads-us-md/regions/us-md.json)")
    parser.add_argument("--out", default=None, help="output .pmtiles path (default: dist/<region>-roads.pmtiles)")
    parser.add_argument("--planet", default=None, help="planet archive URL or local path (default: the newest daily build)")
    parser.add_argument("--planet-date", default=None, help="pin a build date, YYYYMMDD")
    parser.add_argument("--maxzoom", type=int, default=None, help="max zoom (default: the region file's, else 14)")
    parser.add_argument("--minzoom", type=int, default=None, help="min zoom (default: the CLI's own)")
    parser.add_argument("--download-threads", type=int, default=8, help="parallel range-request threads (default: 8)")
    parser.add_argument("--dry-run", action="store_true", help="have pmtiles report the tiles and bytes without downloading")
    args = parser.parse_args(argv)

    root = util.repo_root()
    region = load_region(root, args.region)
    pmtiles = util.require_tool("pmtiles", PMTILES_HINT)

    if args.planet:
        planet = args.planet
    else:
        date = args.planet_date or latest_build_date()
        planet = PLANET_URL.format(date=date)
        util.info(f"planet build: {planet}")

    out = Path(args.out) if args.out else root / "dist" / f"{region['id']}-roads.pmtiles"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)

    bbox = ",".join(str(v) for v in region["bbox"])
    maxzoom = args.maxzoom if args.maxzoom is not None else int(region.get("maxzoom", 14))

    cmd = [
        pmtiles,
        "extract",
        planet,
        str(out),
        f"--bbox={bbox}",
        f"--maxzoom={maxzoom}",
        f"--download-threads={args.download_threads}",
    ]
    if args.minzoom is not None:
        cmd.append(f"--minzoom={args.minzoom}")
    if args.dry_run:
        cmd.append("--dry-run")

    result = util.run(cmd, check=False)
    if result.returncode != 0:
        util.fail(f"pmtiles extract failed with exit code {result.returncode}")

    if args.dry_run:
        util.info("dry run: nothing was written")
        return 0

    if not out.exists():
        util.fail(f"pmtiles extract reported success but {out} is not there")

    size, digest = util.size_and_sha256(out)
    util.info("")
    util.info(f"wrote {out.resolve()}")
    util.info(f"region {region.get('name', region['id'])} · bbox {bbox} · maxzoom {maxzoom}")
    util.info(f"size   {size} ({util.human_bytes(size)})")
    util.info(f"sha256 {digest}")
    util.info(f"license {region.get('license', 'ODbL-1.0')} · attribution {region.get('attribution', '© OpenStreetMap contributors')}")
    util.info("")
    util.info("This file is HOSTED by us (see the hosting note at the top of this script).")
    util.info("Next: upload it to a release and run scripts/update_manifest.py --id maps-roads-<region> --file <this file> --url <release url>")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
