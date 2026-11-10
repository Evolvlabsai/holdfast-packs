# maps-roads-us-ne — Nebraska: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **115 MB** for Nebraska at maxzoom 14
  (98,739 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ne --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ne --out dist/us-ne-roads.pmtiles
```

The bbox is `[-104.06, 39.99, -95.30, 43.01]` from `packs/maps-roads-us-md/regions/us-ne.json`; its
`notes` say how it was chosen.
