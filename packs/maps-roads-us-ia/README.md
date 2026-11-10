# maps-roads-us-ia — Iowa: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **159 MB** for Iowa at maxzoom 14
  (76,758 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ia --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ia --out dist/us-ia-roads.pmtiles
```

The bbox is `[-96.64, 40.37, -90.14, 43.51]` from `packs/maps-roads-us-md/regions/us-ia.json`; its
`notes` say how it was chosen.
