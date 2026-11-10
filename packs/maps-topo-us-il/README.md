# maps-topo-us-il — Illinois: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-il-topo.pmtiles`, 549 MB (5,297 tiles, z5–12).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, z5–12, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-91.52, 36.97, -87.49, 42.51]` present. Metadata name: `"Illinois terrain"`.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (35 cells, ~1,869 MB).

## Building it

```
python scripts/build_topo.py --region us-il --source 1 --dry-run
python scripts/build_topo.py --region us-il --source 1 --out dist/us-il-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
