# maps-roads-us-ut — Utah: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **139 MB** for Utah at maxzoom 14
  (91,016 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ut --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ut --out dist/us-ut-roads.pmtiles
```

The bbox is `[-114.06, 36.99, -109.04, 42.01]` from `packs/maps-roads-us-md/regions/us-ut.json`; its
`notes` say how it was chosen.
