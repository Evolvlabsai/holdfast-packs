# maps-roads-us-ks — Kansas: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **128 MB** for Kansas at maxzoom 14
  (80,313 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ks --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ks --out dist/us-ks-roads.pmtiles
```

The bbox is `[-102.06, 36.99, -94.58, 40.01]` from `packs/maps-roads-us-md/regions/us-ks.json`; its
`notes` say how it was chosen.
