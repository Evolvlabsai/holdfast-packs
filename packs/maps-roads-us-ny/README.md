# maps-roads-us-ny — New York: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **605 MB** for New York at maxzoom 14
  (136,444 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ny --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ny --out dist/us-ny-roads.pmtiles
```

The bbox is `[-79.77, 40.49, -71.85, 45.02]` from `packs/maps-roads-us-md/regions/us-ny.json`; its
`notes` say how it was chosen.
