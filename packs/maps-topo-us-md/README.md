# maps-topo-us-md — Maryland: topo + terrain

Contours and hillshade for off-road travel.

- **Hosting:** ours, per region. ~900 MB for Maryland.
- **Format:** `pmtiles`.
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## NOT BUILT

`scripts/build_topo.py` is a TODO stub: it prints its inputs, steps and outputs,
then exits 2. Read it before starting the work — it is the specification.

In short: 1/3 arc-second 3DEP tiles for the state bbox → GDAL mosaic and warp →
`gdal_contour` at 40 ft plus `gdaldem hillshade` → tippecanoe / gdal2tiles →
`pmtiles convert`.

## The decision that blocks it

A PMTiles archive holds one tile type, and a manifest pack has one `url`.
Contours are vector tiles; hillshade is raster. They cannot share a file. So
this is either **two packs** (`maps-topo-us-md` and `maps-hillshade-us-md`) or
**contours only**, with the phone deriving shading from a terrain-RGB raster that
needs its own encoding decision. **Not decided.**

## Why the weekly job does not build it

GDAL and tippecanoe roughly double `update.yml`'s setup time, and 3DEP changes
quarterly at best. `check_upstream.py` reports this pack as `manual`, and
rebuilding it is a deliberate `workflow_dispatch` with `packs: maps-topo-us-md`.
