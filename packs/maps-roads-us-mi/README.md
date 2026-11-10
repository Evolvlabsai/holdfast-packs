# maps-roads-us-mi — Michigan: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **518 MB** for Michigan at maxzoom 14
  (206,558 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-mi --dry-run     # what it would cost
python scripts/extract_maps.py --region us-mi --out dist/us-mi-roads.pmtiles
```

The bbox is `[-90.42, 41.69, -82.41, 48.23]` from `packs/maps-roads-us-md/regions/us-mi.json`; its
`notes` say how it was chosen.
