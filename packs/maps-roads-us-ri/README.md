# maps-roads-us-ri — Rhode Island: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **40 MB** for Rhode Island at maxzoom 14
  (2,775 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ri --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ri --out dist/us-ri-roads.pmtiles
```

The bbox is `[-71.91, 41.14, -71.11, 42.02]` from `packs/maps-roads-us-md/regions/us-ri.json`; its
`notes` say how it was chosen.
