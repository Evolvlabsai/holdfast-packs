# maps-roads-us-ms — Mississippi: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **109 MB** for Mississippi at maxzoom 14
  (57,212 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ms --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ms --out dist/us-ms-roads.pmtiles
```

The bbox is `[-91.66, 30.17, -88.09, 35.00]` from `packs/maps-roads-us-md/regions/us-ms.json`; its
`notes` say how it was chosen.
