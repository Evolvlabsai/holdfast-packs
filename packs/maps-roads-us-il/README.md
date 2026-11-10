# maps-roads-us-il — Illinois: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **290 MB** for Illinois at maxzoom 14
  (81,519 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-il --dry-run     # what it would cost
python scripts/extract_maps.py --region us-il --out dist/us-il-roads.pmtiles
```

The bbox is `[-91.52, 36.97, -87.49, 42.51]` from `packs/maps-roads-us-md/regions/us-il.json`; its
`notes` say how it was chosen.
