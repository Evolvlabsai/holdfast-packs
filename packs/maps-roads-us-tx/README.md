# maps-roads-us-tx — Texas: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **660 MB** for Texas at maxzoom 14
  (456,791 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-tx --dry-run     # what it would cost
python scripts/extract_maps.py --region us-tx --out dist/us-tx-roads.pmtiles
```

The bbox is `[-106.65, 25.83, -93.50, 36.51]` from `packs/maps-roads-us-md/regions/us-tx.json`; its
`notes` say how it was chosen.
