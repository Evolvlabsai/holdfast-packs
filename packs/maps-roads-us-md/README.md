# maps-roads-us-md — Maryland: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** **ours** — see the correction below. **214 MB** for Maryland at
  maxzoom 14, measured with `--dry-run` against the 2026-11-08 planet build
  (29,738 region tiles, 224 MB transferred, 96 HTTP requests, under two
  seconds). The spec's 310 MB estimate is high; the Packs screen can say 214 MB.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-md --dry-run     # what it would cost
python scripts/extract_maps.py --region us-md --out dist/us-md-roads.pmtiles
```

It calls `pmtiles extract` from protomaps/go-pmtiles against the current daily
planet build. That reads the remote archive over HTTP range requests, so a state
costs a few hundred MB of transfer rather than the whole planet.

Regions are files in `regions/`. Adding a state is one file there plus one
manifest entry; see "How to add a state" in the repository README.

## CORRECTION TO THE SPEC — this pack is Hosted, not Linked

The spec's pack table calls roads **Linked**, sourced from "OpenStreetMap via
Geofabrik or Protomaps". Neither publishes a per-state PMTiles file:

- **Protomaps** publishes one daily *planet* archive. Verified 2026-11-09:
  `https://build.protomaps.com/20261108.pmtiles`, 139,369,055,252 bytes
  (~130 GiB). A phone cannot stream that offline, and a manifest pack has one
  `url` with no way to say "range-read this slice of it".
- **Geofabrik** publishes per-state `.osm.pbf` *data*, not tiles. Turning that
  into tiles is a build step (planetiler or tilemaker), not a link.

So we build the extract and host it, exactly like topo and routing. The cost is
214 MB of release storage and bandwidth per state. It stays free inside
GitHub's acceptable-use policy and moves to Cloudflare R2 through the `mirrors`
field if one state ever draws real traffic. Still $0 — just not the "somebody
else hosts it" that *Linked* implies. The spec's hosting table should be
corrected.
