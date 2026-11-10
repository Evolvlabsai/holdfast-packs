# maps-topo-us-tx — Texas: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-tx-topo.pmtiles`, 759 MB (7,364 tiles, z5–11).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, **z5–11**, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-106.65, 25.83, -93.50, 36.51]` present. Metadata name: `"Texas terrain"`.

## maxzoom 11, not 12 (size limit)

At z12 Texas is 28,957 tiles and the archive came out at **2,692,276,029 bytes
(2.5 GiB)**, over GitHub's 2 GiB per-asset limit. It is therefore built with
`--maxzoom 11`: 7,364 tiles, ~65 m pixels (2x2 box-averaged 1 arc-second cells).
MapLibre overzooms the z11 tiles past z11, so hillshade and contours are a
little softer than in other states; summits read up to ~30 m low (Guadalupe
Peak decodes as 2,638 m against 2,667 m).

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (202 cells including one ring of neighbouring cells, ~8,177 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 168 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (224 cells in all, 202 published by USGS, ~8,177 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 33 of 572 edge tiles changed (at z11 the edge tiles already stayed inside fetched cells; the fixes are in lower-zoom tiles, which reach further past the bbox, e.g. 35.846, -92.998 at z9: 0 m before, 668.6 m now); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 759,368,379 bytes (was 758,611,258), sha256 `495dd5aad2d65c986232d418e5cbe68b199fd9feae1e919426ff34ac39c31d96`.

## Building it

```
python scripts/build_topo.py --region us-tx --source 1 --maxzoom 11 --dry-run
python scripts/build_topo.py --region us-tx --source 1 --maxzoom 11 --out dist/us-tx-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
