# maps-roads-us-wy — Wyoming: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **122 MB** for Wyoming at maxzoom 14
  (107,485 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-wy --dry-run     # what it would cost
python scripts/extract_maps.py --region us-wy --out dist/us-wy-roads.pmtiles
```

The bbox is `[-111.06, 40.99, -104.05, 45.01]` from `packs/maps-roads-us-md/regions/us-wy.json`; its
`notes` say how it was chosen.
