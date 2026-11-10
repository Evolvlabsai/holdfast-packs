# maps-roads-us-wv — West Virginia: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **289 MB** for West Virginia at maxzoom 14
  (60,806 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-wv --dry-run     # what it would cost
python scripts/extract_maps.py --region us-wv --out dist/us-wv-roads.pmtiles
```

The bbox is `[-82.65, 37.20, -77.72, 40.64]` from `packs/maps-roads-us-md/regions/us-wv.json`; its
`notes` say how it was chosen.
