# maps-topo-us-ak — Alaska: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-ak-topo.pmtiles`, 1,291 MB (23,957 tiles, z5–10).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

The same contract as Maryland's (`packs/maps-topo-us-md/README.md`): one
PMTiles v3 archive of Terrarium-encoded raster-dem PNG tiles, **z5–10**, 256 px,
`height_m = (R*256 + G + B/256) - 32768`, sea and no-data 0 m, every tile
intersecting the bbox `[-180.00, 51.20, -129.97, 71.40]` present. Metadata name: `"Alaska terrain"`.

## maxzoom 10 (size limit)

Alaska is enormous in Web Mercator. At z11 it is 95,207 tiles (four times z10's
23,957), roughly 5 GB, far over GitHub's 2 GiB per-asset limit. z10 is
**1,290,605,142 bytes**, so the pack stops at z10 (~75 m pixels at Anchorage's
latitude, 1 arc-second cells box-averaged 2x2). MapLibre overzooms past z10;
summits read a little low (Denali decodes as 6,153 m against 6,190 m).

## Antimeridian

**Antimeridian:** the bbox is clipped at -180. Web Mercator tile ranges and a PMTiles bbox cannot wrap, so the western Aleutians west of 180 degrees (the Rat and Near Islands: Attu, Agattu, Shemya, Kiska, Amchitka, Semisopochnoi) are not in this pack.

## Coverage: 1 arc-second is statewide

The 3DEP 1 arc-second product covers every Alaska cell in the box (587 cells
published, ~22.5 GB). The 2 arc-second Alaska product (`--source 2`) has 504,
a subset, apart from two cells: n63w141 (Yukon, just east of the 141st
meridian) and n69w168 (Chukchi Sea). With `--source 1`, n63w141 is therefore
0 m: a 1x1 degree patch of Yukon inside the box but outside Alaska. Gulf of
Alaska, Beaufort Sea and Pacific cells are unpublished and 0 m, as everywhere.

## Source: 1 arc-second, not 1/3

Unlike Maryland, this pack is built from the **1 arc-second** (~30 m) 3DEP
product (`--source 1`). At z12 a pixel is already ~30 m, so the finer product
only buys a box average; the 1 arc-second cells are about a ninth of the
download (587 cells including one ring of neighbouring cells, ~22,469 MB).

## Building it

```
python scripts/build_topo.py --region us-ak --source 1 --maxzoom 10 --dry-run
python scripts/build_topo.py --region us-ak --source 1 --maxzoom 10 --out dist/us-ak-topo.pmtiles
```

Cells are cached in `../holdfast-dist/topo-cache` as `USGS_1_<cell>.tif`.
