# maps-roads-us-mo — Missouri: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **276 MB** for Missouri at maxzoom 14
  (110,557 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-mo --dry-run     # what it would cost
python scripts/extract_maps.py --region us-mo --out dist/us-mo-roads.pmtiles
```

The bbox is `[-95.78, 35.99, -89.09, 40.62]` from `packs/maps-roads-us-md/regions/us-mo.json`; its
`notes` say how it was chosen.
