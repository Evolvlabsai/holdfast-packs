# maps-topo-us-mn — Minnesota: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-mn-topo.pmtiles`, 1,076 MB (11,905 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-97.24, 43.49, -89.48, 49.39]` present. Metadata name: `"Minnesota terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (99 cells including one ring of neighbouring cells, ~4,344 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 63 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (99 cells in all, 99 published by USGS, ~4,344 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 36 of 748 edge tiles changed (at z12 the edge tiles already stayed inside fetched cells; the fixes are in lower-zoom tiles, which reach further past the bbox, e.g. 43.159, -98.083 at z8: 0 m before, 578.5 m now); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 1,075,795,364 bytes (was 1,074,680,801), sha256 `a877e76504dc7f6cabdce9e9d6dbfb094147d999073f3717a9cac97062eae5aa`.

## Building it

```
python scripts/build_topo.py --region us-mn --source 1 --dry-run
python scripts/build_topo.py --region us-mn --source 1 --out dist/us-mn-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
