# maps-topo-us-ar — Arkansas: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-ar-topo.pmtiles`, 403 MB (3,886 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-94.62, 33.00, -89.64, 36.50]` present. Metadata name: `"Arkansas terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (48 cells including one ring of neighbouring cells, ~2,721 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 24 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (48 cells in all, 48 published by USGS, ~2,721 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 132 of 420 edge tiles changed (504,832 pixels just outside the bbox went from 0 m to real terrain at z12); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 402,678,570 bytes (was 398,793,090), sha256 `dbf73a13a6a592156d78513c350e62727e167e0a39593c52db82506f0b58563d`.

## Building it

```
python scripts/build_topo.py --region us-ar --source 1 --dry-run
python scripts/build_topo.py --region us-ar --source 1 --out dist/us-ar-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
