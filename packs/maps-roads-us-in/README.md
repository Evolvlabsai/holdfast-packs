# maps-roads-us-in — Indiana: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **192 MB** for Indiana at maxzoom 14
  (48,387 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-in --dry-run     # what it would cost
python scripts/extract_maps.py --region us-in --out dist/us-in-roads.pmtiles
```

The bbox is `[-88.10, 37.77, -84.78, 41.77]` from `packs/maps-roads-us-md/regions/us-in.json`; its
`notes` say how it was chosen.
