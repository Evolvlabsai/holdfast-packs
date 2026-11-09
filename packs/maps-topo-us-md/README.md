# maps-topo-us-md — Maryland: terrain

Elevation for off-road travel. The phone draws hillshade and contours from it.

- **Hosting:** ours, per region.
- **Format:** `pmtiles` — **one file**, `us-md-topo.pmtiles`, ~196 MB (1,996 tiles).
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

## Building it

```
python -m pip install --user -r scripts/requirements.txt
python scripts/build_topo.py --region us-md --dry-run
python scripts/build_topo.py --region us-md --out dist/us-md-topo.pmtiles
```

No GDAL and no tippecanoe: tifffile + imagecodecs read the USGS 3DEP 1/3
arc-second GeoTIFFs, numpy resamples them to Mercator, Pillow writes the PNGs and
the `pmtiles` package writes the archive. The 15 source cells for Maryland are
~6.1 GB and are cached (conditional GET) in `../holdfast-dist/topo-cache` unless
`--cache-dir` says otherwise. The script's docstring has the full steps.

## Why the weekly job does not build it

It downloads ~6 GB and 3DEP changes quarterly at best. `check_upstream.py`
reports this pack as `manual`, and rebuilding it is a deliberate
`workflow_dispatch` with `packs: maps-topo-us-md`.
