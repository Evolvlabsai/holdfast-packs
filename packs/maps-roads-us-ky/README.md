# maps-roads-us-ky — Kentucky: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **205 MB** for Kentucky at maxzoom 14
  (72,026 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ky --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ky --out dist/us-ky-roads.pmtiles
```

The bbox is `[-89.58, 36.49, -81.96, 39.15]` from `packs/maps-roads-us-md/regions/us-ky.json`; its
`notes` say how it was chosen.
