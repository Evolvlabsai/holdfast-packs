# maps-roads-us-la — Louisiana: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **147 MB** for Louisiana at maxzoom 14
  (70,530 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-la --dry-run     # what it would cost
python scripts/extract_maps.py --region us-la --out dist/us-la-roads.pmtiles
```

The bbox is `[-94.05, 28.92, -88.81, 33.02]` from `packs/maps-roads-us-md/regions/us-la.json`; its
`notes` say how it was chosen.
