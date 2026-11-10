# maps-topo-us-ut — Utah: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-ut-topo.pmtiles`, 683 MB (5,859 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-114.06, 36.99, -109.04, 42.01]` present. Metadata name: `"Utah terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (72 cells including one ring of neighbouring cells, ~3,573 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 42 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (72 cells in all, 72 published by USGS, ~3,573 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 167 of 520 edge tiles changed (883,200 pixels just outside the bbox went from 0 m to real terrain at z12); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 683,384,488 bytes (was 680,306,164), sha256 `a5b39c9adaa0df9cc7d02fe9ca5969950bcf1dff2837bf388ca3f4fd96b3f451`.

## Building it

```
python scripts/build_topo.py --region us-ut --source 1 --dry-run
python scripts/build_topo.py --region us-ut --source 1 --out dist/us-ut-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
