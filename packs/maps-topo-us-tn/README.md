# maps-topo-us-tn — Tennessee: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-tn-topo.pmtiles`, 412 MB (3,414 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-90.32, 34.98, -81.64, 36.68]` present. Metadata name: `"Tennessee terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (60 cells including one ring of neighbouring cells, ~3,455 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 30 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (60 cells in all, 60 published by USGS, ~3,455 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 35 of 490 edge tiles changed (at z12 the edge tiles already stayed inside fetched cells; the fixes are in lower-zoom tiles, which reach further past the bbox, e.g. 37.05, -81.616 at z9: 0 m before, 1,348.2 m now); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 411,575,595 bytes (was 409,824,715), sha256 `b575541765ca6ded0b1b6cbc08ac7949cf2c190b551fae39fa23f0d99aff5bd9`.

## Building it

```
python scripts/build_topo.py --region us-tn --source 1 --dry-run
python scripts/build_topo.py --region us-tn --source 1 --out dist/us-tn-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
