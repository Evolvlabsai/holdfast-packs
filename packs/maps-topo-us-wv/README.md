# maps-topo-us-wv — West Virginia: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-wv-topo.pmtiles`, 514 MB (3,938 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-82.65, 37.20, -77.72, 40.64]` present. Metadata name: `"West Virginia terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (48 cells including one ring of neighbouring cells, ~2,682 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 24 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (48 cells in all, 48 published by USGS, ~2,682 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 13 of 418 edge tiles changed (at z12 the edge tiles already stayed inside fetched cells; the fixes are in lower-zoom tiles, which reach further past the bbox, e.g. 36.662, -81.543 at z8: 0 m before, 1,699.0 m now); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 514,456,529 bytes (was 513,918,787), sha256 `c9a72de4ce805be274d7f1c956ee2b59fc2443e636d7b2fab0e25ce8e3512596`.

## Building it

```
python scripts/build_topo.py --region us-wv --source 1 --dry-run
python scripts/build_topo.py --region us-wv --source 1 --out dist/us-wv-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
