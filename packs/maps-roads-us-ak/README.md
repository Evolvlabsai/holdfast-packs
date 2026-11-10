# maps-roads-us-ak — Alaska: roads

Streets, trails, points of interest and place search, as one PMTiles archive.

- **Hosting:** ours, like Maryland's (see `packs/maps-roads-us-md/README.md` for
  why roads is Hosted, not Linked). **744 MB** for Alaska at maxzoom 14
  (6,068,684 region tiles), extracted 2026-11-09 from the
  20261108 planet build.
- **Format:** `pmtiles`.
- **Cadence:** monthly.
- **`staleAfterDays`:** 90.
- **Licence:** ODbL 1.0. The OpenStreetMap credit must appear **on the map**,
  not only on an About screen.

**Antimeridian:** the bbox is clipped at -180. Web Mercator tile ranges and a PMTiles bbox cannot wrap, so the western Aleutians west of 180 degrees (the Rat and Near Islands: Attu, Agattu, Shemya, Kiska, Amchitka, Semisopochnoi) are not in this pack.

## Build

```bash
python scripts/extract_maps.py --region us-ak --dry-run     # what it would cost
python scripts/extract_maps.py --region us-ak --out dist/us-ak-roads.pmtiles
```

The bbox is `[-180.00, 51.20, -129.97, 71.40]` from `packs/maps-roads-us-md/regions/us-ak.json`; its
`notes` say how it was chosen.
