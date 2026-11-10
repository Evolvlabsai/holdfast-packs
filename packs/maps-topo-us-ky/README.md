# maps-topo-us-ky — Kentucky: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-ky-topo.pmtiles`, 557 MB (4,664 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-89.58, 36.49, -81.96, 39.15]` present. Metadata name: `"Kentucky terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (66 cells including one ring of neighbouring cells, ~3,733 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 36 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (66 cells in all, 66 published by USGS, ~3,733 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 17 of 497 edge tiles changed (at z12 the edge tiles already stayed inside fetched cells; the fixes are in lower-zoom tiles, which reach further past the bbox, e.g. 35.561, -83.499 at z8: 0 m before, 1,970.4 m now); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 556,865,556 bytes (was 555,909,980), sha256 `9b8f1b9629a7c603e58c7b5779bafd82c12f6aa671e94a51ff6ee97d4f455d03`.

## Building it

```
python scripts/build_topo.py --region us-ky --source 1 --dry-run
python scripts/build_topo.py --region us-ky --source 1 --out dist/us-ky-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
