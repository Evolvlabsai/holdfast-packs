# maps-roads-us-nh — New Hampshire: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **87 MB** for New Hampshire at maxzoom 14
  (20,232 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-nh --dry-run     # what it would cost
python scripts/extract_maps.py --region us-nh --out dist/us-nh-roads.pmtiles
```

The bbox is `[-72.56, 42.69, -70.60, 45.31]` from `packs/maps-roads-us-md/regions/us-nh.json`; its
`notes` say how it was chosen.
