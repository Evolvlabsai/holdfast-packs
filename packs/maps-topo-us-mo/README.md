# maps-topo-us-mo — Missouri: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-mo-topo.pmtiles`, 784 MB (7,121 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-95.78, 35.99, -89.09, 40.62]` present. Metadata name: `"Missouri terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (42 cells, ~2,320 MB).

## Building it

```
python scripts/build_topo.py --region us-mo --source 1 --dry-run
python scripts/build_topo.py --region us-mo --source 1 --out dist/us-mo-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
