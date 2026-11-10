# maps-roads-us-mt — Montana: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **192 MB** for Montana at maxzoom 14
  (227,698 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

## Build

```bash
python scripts/extract_maps.py --region us-mt --dry-run     # what it would cost
python scripts/extract_maps.py --region us-mt --out dist/us-mt-roads.pmtiles
```

The bbox is `[-116.05, 44.35, -104.03, 49.01]` from `packs/maps-roads-us-md/regions/us-mt.json`; its
`notes` say how it was chosen.
