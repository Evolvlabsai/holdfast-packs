# maps-topo-us-ok — Oklahoma: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-ok-topo.pmtiles`, 670 MB (6,429 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-103.01, 33.61, -94.43, 37.01]` present. Metadata name: `"Oklahoma terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (84 cells including one ring of neighbouring cells, ~4,219 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 50 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (84 cells in all, 84 published by USGS, ~4,219 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 22 of 580 edge tiles changed (at z12 the edge tiles already stayed inside fetched cells; the fixes are in lower-zoom tiles, which reach further past the bbox, e.g. 36.811, -104.049 at z8: 0 m before, 2,408.1 m now); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 670,180,655 bytes (was 669,377,929), sha256 `9dc68dccba88ccb703dc4303c0f262911e4445d35b36249094e4985fbf3fe70f`.

## Building it

```
python scripts/build_topo.py --region us-ok --source 1 --dry-run
python scripts/build_topo.py --region us-ok --source 1 --out dist/us-ok-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
