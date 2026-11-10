# maps-roads-us-wa — Washington: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **288 MB** for Washington at maxzoom 14
  (112,439 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-wa --dry-run     # what it would cost
python scripts/extract_maps.py --region us-wa --out dist/us-wa-roads.pmtiles
```

The bbox is `[-124.77, 45.54, -116.91, 49.01]` from `packs/maps-roads-us-md/regions/us-wa.json`; its
`notes` say how it was chosen.
