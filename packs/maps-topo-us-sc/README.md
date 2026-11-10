# maps-topo-us-sc — South Carolina: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-sc-topo.pmtiles`, 309 MB (3,384 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-83.36, 32.03, -78.49, 35.22]` present. Metadata name: `"South Carolina terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (43 cells including one ring of neighbouring cells, ~2,245 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 24 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (48 cells in all, 43 published by USGS, ~2,245 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 47 of 392 edge tiles changed (at z12 the edge tiles already stayed inside fetched cells; the fixes are in lower-zoom tiles, which reach further past the bbox, e.g. 31.977, -83.484 at z11: 0 m before, 127.1 m now); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 308,697,038 bytes (was 307,603,627), sha256 `15abae8d83e05e6f57f19ddc046b3f0f676c4f51bbad8dab5af9b9e60167d731`.

## Building it

```
python scripts/build_topo.py --region us-sc --source 1 --dry-run
python scripts/build_topo.py --region us-sc --source 1 --out dist/us-sc-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
