# maps-roads-us-co — Colorado: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **250 MB** for Colorado at maxzoom 14
  (101,372 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-co --dry-run     # what it would cost
python scripts/extract_maps.py --region us-co --out dist/us-co-roads.pmtiles
```

The bbox is `[-109.07, 36.99, -102.04, 41.01]` from `packs/maps-roads-us-md/regions/us-co.json`; its
`notes` say how it was chosen.
