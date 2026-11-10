# maps-roads-us-ga — Georgia: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **336 MB** for Georgia at maxzoom 14
  (74,256 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ga --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ga --out dist/us-ga-roads.pmtiles
```

The bbox is `[-85.61, 30.35, -80.83, 35.01]` from `packs/maps-roads-us-md/regions/us-ga.json`; its
`notes` say how it was chosen.
