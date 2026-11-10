# maps-roads-us-hi — Hawaii: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **15 MB** for Hawaii at maxzoom 14
  (54,354 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-hi --dry-run     # what it would cost
python scripts/extract_maps.py --region us-hi --out dist/us-hi-roads.pmtiles
```

The bbox is `[-160.26, 18.90, -154.80, 22.24]` from `packs/maps-roads-us-md/regions/us-hi.json`; its
`notes` say how it was chosen.
