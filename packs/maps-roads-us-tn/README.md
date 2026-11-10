# maps-roads-us-tn — Tennessee: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **180 MB** for Tennessee at maxzoom 14
  (51,189 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-tn --dry-run     # what it would cost
python scripts/extract_maps.py --region us-tn --out dist/us-tn-roads.pmtiles
```

The bbox is `[-90.32, 34.98, -81.64, 36.68]` from `packs/maps-roads-us-md/regions/us-tn.json`; its
`notes` say how it was chosen.
