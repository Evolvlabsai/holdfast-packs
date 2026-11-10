# maps-roads-us-nc — North Carolina: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **371 MB** for North Carolina at maxzoom 14
  (83,362 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-nc --dry-run     # what it would cost
python scripts/extract_maps.py --region us-nc --out dist/us-nc-roads.pmtiles
```

The bbox is `[-84.33, 33.84, -75.45, 36.59]` from `packs/maps-roads-us-md/regions/us-nc.json`; its
`notes` say how it was chosen.
