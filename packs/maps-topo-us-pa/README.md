# maps-topo-us-pa — Pennsylvania: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-pa-topo.pmtiles`, 437 MB (3,620 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-80.52, 39.71, -74.69, 42.27]` present. Metadata name: `"Pennsylvania terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (52 cells including one ring of neighbouring cells, ~2,527 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 28 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (54 cells in all, 52 published by USGS, ~2,527 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 26 of 422 edge tiles changed (at z12 the edge tiles already stayed inside fetched cells; the fixes are in lower-zoom tiles, which reach further past the bbox, e.g. 38.927, -79.423 at z8: 0 m before, 1,427.7 m now); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 436,739,470 bytes (was 436,151,248), sha256 `845e886765d1da4c784f9cef28a10bf9d3cbf89d967be7fbdc03732edf9a61a7`.

## Building it

```
python scripts/build_topo.py --region us-pa --source 1 --dry-run
python scripts/build_topo.py --region us-pa --source 1 --out dist/us-pa-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
