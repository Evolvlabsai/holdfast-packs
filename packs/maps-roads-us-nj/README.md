# maps-roads-us-nj — New Jersey: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **154 MB** for New Jersey at maxzoom 14
  (15,288 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-nj --dry-run     # what it would cost
python scripts/extract_maps.py --region us-nj --out dist/us-nj-roads.pmtiles
```

The bbox is `[-75.57, 38.92, -73.88, 41.36]` from `packs/maps-roads-us-md/regions/us-nj.json`; its
`notes` say how it was chosen.
