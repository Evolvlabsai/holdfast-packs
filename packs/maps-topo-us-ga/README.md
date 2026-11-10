# maps-topo-us-ga — Georgia: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-ga-topo.pmtiles`, 512 MB (4,874 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-85.61, 30.35, -80.83, 35.01]` present. Metadata name: `"Georgia terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (59 cells including one ring of neighbouring cells, ~3,055 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 36 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (64 cells in all, 59 published by USGS, ~3,055 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 18 of 472 edge tiles changed (at z12 the edge tiles already stayed inside fetched cells; the fixes are in lower-zoom tiles, which reach further past the bbox, e.g. 29.919, -82.032 at z8: 0 m before, 76.6 m now); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 511,978,004 bytes (was 511,456,569), sha256 `814ee6f362d4545fbcececec0a4c1d67a875f18c5b76d5d4d6f9438eb5d8d8ed`.

## Building it

```
python scripts/build_topo.py --region us-ga --source 1 --dry-run
python scripts/build_topo.py --region us-ga --source 1 --out dist/us-ga-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
