# maps-roads-us-me — Maine: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **136 MB** for Maine at maxzoom 14
  (74,287 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-me --dry-run     # what it would cost
python scripts/extract_maps.py --region us-me --out dist/us-me-roads.pmtiles
```

The bbox is `[-71.09, 42.97, -66.94, 47.46]` from `packs/maps-roads-us-md/regions/us-me.json`; its
`notes` say how it was chosen.
