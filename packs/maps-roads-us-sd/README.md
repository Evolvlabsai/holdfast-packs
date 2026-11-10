# maps-roads-us-sd — South Dakota: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **79 MB** for South Dakota at maxzoom 14
  (103,136 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-sd --dry-run     # what it would cost
python scripts/extract_maps.py --region us-sd --out dist/us-sd-roads.pmtiles
```

The bbox is `[-104.06, 42.47, -96.43, 45.95]` from `packs/maps-roads-us-md/regions/us-sd.json`; its
`notes` say how it was chosen.
