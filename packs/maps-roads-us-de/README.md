# maps-roads-us-de — Delaware: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **29 MB** for Delaware at maxzoom 14
  (3,919 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-de --dry-run     # what it would cost
python scripts/extract_maps.py --region us-de --out dist/us-de-roads.pmtiles
```

The bbox is `[-75.79, 38.45, -75.04, 39.84]` from `packs/maps-roads-us-md/regions/us-de.json`; its
`notes` say how it was chosen.
