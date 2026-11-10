# maps-roads-us-ca — California: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **627 MB** for California at maxzoom 14
  (340,965 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-ca --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ca --out dist/us-ca-roads.pmtiles
```

The bbox is `[-124.42, 32.53, -114.13, 42.01]` from `packs/maps-roads-us-md/regions/us-ca.json`; its
`notes` say how it was chosen.
