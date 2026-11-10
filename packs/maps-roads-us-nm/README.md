# maps-roads-us-nm — New Mexico: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **135 MB** for New Mexico at maxzoom 14
  (116,335 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-nm --dry-run     # what it would cost
python scripts/extract_maps.py --region us-nm --out dist/us-nm-roads.pmtiles
```

The bbox is `[-109.06, 31.33, -103.00, 37.01]` from `packs/maps-roads-us-md/regions/us-nm.json`; its
`notes` say how it was chosen.
