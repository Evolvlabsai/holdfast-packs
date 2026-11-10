# maps-roads-us-ma — Massachusetts: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **213 MB** for Massachusetts at maxzoom 14
  (22,573 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ma --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ma --out dist/us-ma-roads.pmtiles
```

The bbox is `[-73.51, 41.23, -69.92, 42.89]` from `packs/maps-roads-us-md/regions/us-ma.json`; its
`notes` say how it was chosen.
