# maps-roads-us-ar — Arkansas: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **116 MB** for Arkansas at maxzoom 14
  (59,624 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ar --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ar --out dist/us-ar-roads.pmtiles
```

The bbox is `[-94.62, 33.00, -89.64, 36.50]` from `packs/maps-roads-us-md/regions/us-ar.json`; its
`notes` say how it was chosen.
