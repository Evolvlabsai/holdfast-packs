# maps-roads-us-fl — Florida: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **609 MB** for Florida at maxzoom 14
  (155,574 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-fl --dry-run     # what it would cost
python scripts/extract_maps.py --region us-fl --out dist/us-fl-roads.pmtiles
```

The bbox is `[-87.64, 24.52, -80.03, 31.01]` from `packs/maps-roads-us-md/regions/us-fl.json`; its
`notes` say how it was chosen.
