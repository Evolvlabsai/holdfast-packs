# maps-topo-us-md — Maryland: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-md-topo.pmtiles`, 207 MB (1,996 tiles).
- **Cadence:** quarterly.
- **`staleAfterDays`:** 180.
- **Licence:** public domain (USGS 3DEP), credited anyway.

## What is in the file

One PMTiles v3 archive of **Terrarium-encoded raster-dem tiles**:

| | |
|---|---|
| Tiles | Web Mercator XYZ, 256×256 PNG, `tile_compression: none` |
| Zooms | 5–12 (z12 is ~30 m per pixel at Maryland's latitude) |
| Bounds | the region bbox, `[-79.49, 37.88, -75.05, 39.73]` |
| Encoding | `height_m = (R*256 + G + B/256) - 32768`; sea and no-data are 0 m |
| Coverage | every tile intersecting the bbox, ocean included, so no holes |
| Metadata | `{"name": "Maryland terrain", "encoding": "terrarium", "attribution": "USGS 3D Elevation Program (public domain)", "vector_layers": []}` |

## The decision (settled)

A PMTiles archive holds one tile type, and a manifest pack has one `url`.
Rather than two packs (vector contours + raster hillshade), this pack ships
**elevation only**. MapLibre renders hillshade straight from a `raster-dem`
source with `encoding: "terrarium"`, and contours are generated on the device
from the same tiles. One download, one URL, and the style decides how it looks.

## Edge tiles: one ring of neighbouring cells

Rebuilt 2026-11-10 with `build_topo.py`'s cell ring (`CELL_RING = 1`): besides the 15 1x1 degree cells under the bbox, the builder fetches the ring of neighbouring cells (35 cells in all, 33 published by USGS, ~14,250 MB). Before, an edge tile that reached past the bbox into a cell that was not fetched read 0 m there, a flat strip of fake sea along the edge. Now 40 of 312 edge tiles changed (164,166 pixels just outside the bbox went from 0 m to real terrain at z12); every tile lying fully inside the bbox is byte-identical to the previous build. Cells USGS does not publish (open sea) are still 0 m. One ring covers every tile at z9 and above; z5-z8 tiles reaching more than a degree past the bbox are still 0 m out there.

Rebuilt file: 206,540,895 bytes (was 205,119,819), sha256 `7dc07d4615de918a82d9513ea2dc68b6a68fce426575529f3880b2914c3605a0`.

## Building it

```
python -m pip install --user -r scripts/requirements.txt
python scripts/build_topo.py --region us-md --dry-run
python scripts/build_topo.py --region us-md --out dist/us-md-topo.pmtiles
```

No GDAL and no tippecanoe: tifffile + imagecodecs read the USGS 3DEP 1/3
arc-second GeoTIFFs, numpy resamples them to Mercator, Pillow writes the PNGs and
the `pmtiles` package writes the archive. The 33 published source cells for Maryland (35 with the ring, 15 under the bbox) are
~14.2 GB and are cached (conditional GET) in `../holdfast-dist/topo-cache` unless
`--cache-dir` says otherwise. The script's docstring has the full steps.

## Why the weekly job does not build it

It downloads ~6 GB and 3DEP changes quarterly at best. `check_upstream.py`
reports this pack as `manual`, and rebuilding it is a deliberate
`workflow_dispatch` with `packs: maps-topo-us-md`.
