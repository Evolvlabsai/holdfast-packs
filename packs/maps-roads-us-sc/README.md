# maps-roads-us-sc — South Carolina: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **185 MB** for South Carolina at maxzoom 14
  (52,007 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-sc --dry-run     # what it would cost
python scripts/extract_maps.py --region us-sc --out dist/us-sc-roads.pmtiles
```

The bbox is `[-83.36, 32.03, -78.49, 35.22]` from `packs/maps-roads-us-md/regions/us-sc.json`; its
`notes` say how it was chosen.
