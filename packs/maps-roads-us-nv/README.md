# maps-roads-us-nv — Nevada: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **186 MB** for Nevada at maxzoom 14
  (149,316 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-nv --dry-run     # what it would cost
python scripts/extract_maps.py --region us-nv --out dist/us-nv-roads.pmtiles
```

The bbox is `[-120.01, 35.00, -114.03, 42.01]` from `packs/maps-roads-us-md/regions/us-nv.json`; its
`notes` say how it was chosen.
