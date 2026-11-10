# maps-topo-us-dc — District of Columbia: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-dc-topo.pmtiles`, 3.3 MB (30 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-77.12, 38.79, -76.91, 39.00]` present. Metadata name: `"District of Columbia terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (12 cells including one ring of neighbouring cells, ~628 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 2 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (12 cells in all, 12 published by USGS, ~628 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 14 of 28 edge tiles changed (79,872 pixels just outside the bbox went from 0 m to real terrain at z12); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 3,284,767 bytes (was 2,454,559), sha256 `0e23eb9f0585e81030aaa00e40c14cc4b7e8a2f7edfad127a076d009553c3f46`.

## Building it

```
python scripts/build_topo.py --region us-dc --source 1 --dry-run
python scripts/build_topo.py --region us-dc --source 1 --out dist/us-dc-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
