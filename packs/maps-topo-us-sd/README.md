# maps-topo-us-sd — South Dakota: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-sd-topo.pmtiles`, 701 MB (6,561 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-104.06, 42.47, -96.43, 45.95]` present. Metadata name: `"South Dakota terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (66 cells including one ring of neighbouring cells, ~3,331 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 36 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (66 cells in all, 66 published by USGS, ~3,331 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 55 of 556 edge tiles changed (at z12 the edge tiles already stayed inside fetched cells; the fixes are in lower-zoom tiles, which reach further past the bbox, e.g. 46.003, -103.72 at z10: 0 m before, 1,028.5 m now); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 701,185,757 bytes (was 699,388,379), sha256 `9ae7fe06274ed1a0ef53b21bade0e57bf1e11b4c93f01bdcd7c652afc572175b`.

## Building it

```
python scripts/build_topo.py --region us-sd --source 1 --dry-run
python scripts/build_topo.py --region us-sd --source 1 --out dist/us-sd-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
