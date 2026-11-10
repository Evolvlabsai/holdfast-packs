# maps-roads-us-al — Alabama: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **251 MB** for Alabama at maxzoom 14
  (58,449 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-al --dry-run     # what it would cost
python scripts/extract_maps.py --region us-al --out dist/us-al-roads.pmtiles
```

The bbox is `[-88.48, 30.14, -84.88, 35.01]` from `packs/maps-roads-us-md/regions/us-al.json`; its
`notes` say how it was chosen.
