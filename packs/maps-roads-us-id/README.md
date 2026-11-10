# maps-roads-us-id — Idaho: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **211 MB** for Idaho at maxzoom 14
  (174,487 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-id --dry-run     # what it would cost
python scripts/extract_maps.py --region us-id --out dist/us-id-roads.pmtiles
```

The bbox is `[-117.25, 41.98, -111.04, 49.01]` from `packs/maps-roads-us-md/regions/us-id.json`; its
`notes` say how it was chosen.
