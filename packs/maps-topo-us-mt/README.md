# maps-topo-us-mt — Montana: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-mt-topo.pmtiles`, 1,745 MB (14,520 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-116.05, 44.35, -104.03, 49.01]` present. Metadata name: `"Montana terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (120 cells including one ring of neighbouring cells, ~5,783 MB).

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 78 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (120 cells in all, 120 published by USGS, ~5,783 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 182 of 862 edge tiles changed (1,477,632 pixels just outside the bbox went from 0 m to real terrain at z12); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 1,745,307,600 bytes (was 1,734,724,592), sha256 `aa22ea9c6483ae560a2f800a320ad9a2d9ca298d345bc8e0807f38e5fd83dde2`.

## Building it

```
python scripts/build_topo.py --region us-mt --source 1 --dry-run
python scripts/build_topo.py --region us-mt --source 1 --out dist/us-mt-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
