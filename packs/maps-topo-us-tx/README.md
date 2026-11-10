# maps-topo-us-tx — Texas: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-tx-topo.pmtiles`, 759 MB (7,364 tiles, z5–11).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, **z5–11**, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-106.65, 25.83, -93.50, 36.51]` present. Metadata name: `"Texas terrain"`.

## maxzoom 11, not 12 (size limit)

At z12 Texas is 28,957 tiles and the archive came out at **2,692,276,029 bytes
(2.5 GiB)**, over GitHub's 2 GiB per-asset limit. It is therefore built with
`--maxzoom 11`: 7,364 tiles, ~65 m pixels (2x2 box-averaged 1 arc-second cells).
MapLibre overzooms the z11 tiles past z11, so hillshade and contours are a
little softer than in other states; summits read up to ~30 m low (Guadalupe
Peak decodes as 2,638 m against 2,667 m).

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (155 cells, ~6,404 MB).

## Building it

```
python scripts/build_topo.py --region us-tx --source 1 --maxzoom 11 --dry-run
python scripts/build_topo.py --region us-tx --source 1 --maxzoom 11 --out dist/us-tx-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
