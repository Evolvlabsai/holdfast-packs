# maps-topo-us-nv — Nevada: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-nv-topo.pmtiles`, 1,124 MB (9,567 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-120.01, 35.00, -114.03, 42.01]` present. Metadata name: `"Nevada terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (89 cells including one ring of neighbouring cells, ~4,419 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 56 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (90 cells in all, 89 published by USGS, ~4,419 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 348 of 672 edge tiles changed (3,077,659 pixels just outside the bbox went from 0 m to real terrain at z12); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 1,124,154,167 bytes (was 1,109,097,765), sha256 `7a33f48374a23bceaf64e5d3d57f903611b2c4ca1251625d8ce1cdf000b6258c`.

## Building it

```
python scripts/build_topo.py --region us-nv --source 1 --dry-run
python scripts/build_topo.py --region us-nv --source 1 --out dist/us-nv-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
