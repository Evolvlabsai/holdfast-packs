# maps-roads-us-ct — Connecticut: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **79 MB** for Connecticut at maxzoom 14
  (7,977 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ct --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ct --out dist/us-ct-roads.pmtiles
```

The bbox is `[-73.73, 40.98, -71.78, 42.06]` from `packs/maps-roads-us-md/regions/us-ct.json`; its
`notes` say how it was chosen.
