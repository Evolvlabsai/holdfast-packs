#!/usr/bin/env python3
"""TODO (not implemented): build the per-state topo + terrain pack.

Running this script exits 2 and prints the plan below. It is a stub on purpose:
the topo pipeline needs a GDAL toolchain and a tiler, neither of which this repo
installs yet, and a half-working builder that produced a wrong-looking pack
would be worse than one that refuses.

Manifest entry: ``maps-topo-us-md`` -- format ``pmtiles``, Hosted, ~900 MB for
Maryland, quarterly cadence, public domain (USGS), ``staleAfterDays`` 180.

INPUTS
------
1. USGS 3DEP elevation for the state's bbox, from The National Map:
   - 1/3 arc-second (~10 m) seamless DEM is the right trade-off for a phone;
     1 m is far too large per state.
   - Delivery: TNM Access API (``https://tnmaccess.nationalmap.gov/api/v1/products``)
     or the S3 mirror ``s3://prd-tnm/StagedProducts/Elevation/13/TIFF/``.
   - The state's bbox comes from the same region file roads uses:
     ``packs/maps-roads-us-md/regions/<region>.json``.
2. Nothing else. No OSM, no third-party data; this pack stays public domain.

STEPS
-----
1. Download every 1x1 degree 3DEP tile overlapping the bbox (conditional GET;
   reuse ``holdfast.httpcache``).
2. ``gdalbuildvrt`` a mosaic, then ``gdalwarp`` to EPSG:3857 and clip to bbox.
3. Contours: ``gdal_contour -i 12.192`` (40 ft) -> GeoJSON/FlatGeobuf, with an
   index-contour attribute every 5th line so the style can weight them.
4. Hillshade: ``gdaldem hillshade -z 1.5 -compute_edges`` -> single-band GeoTIFF.
5. Tile both:
   - contours (vector) with tippecanoe -> .mbtiles -> ``pmtiles convert``;
   - hillshade (raster) with ``gdal2tiles``/``rio mbtiles`` -> ``pmtiles convert``.
6. Decide ONE output file. MapLibre can read two archives, but the manifest gives
   a pack one URL, so either:
   (a) ship two packs (``maps-topo-us-md``, ``maps-hillshade-us-md``), or
   (b) ship contours only as vector tiles and compute hillshade on device from a
       terrain-RGB raster in the same archive.
   PMTiles v3 holds one tile type per archive, so (a) is the honest option and
   (b) needs a terrain-RGB encoding decision. **Open question -- not decided.**

OUTPUT
------
``dist/<region>-topo.pmtiles``, then:

    gh release upload maps-<yyyy.mm> dist/<region>-topo.pmtiles
    python scripts/update_manifest.py --id maps-topo-<region> \
        --file dist/<region>-topo.pmtiles --url <release asset url> \
        --changes "Rebuilt from the current USGS 3DEP release."

TOOLS NEEDED (none installed yet)
---------------------------------
GDAL >= 3.8 (``gdalbuildvrt``, ``gdalwarp``, ``gdal_contour``, ``gdaldem``),
tippecanoe, go-pmtiles. On Ubuntu runners GDAL and tippecanoe both come from
apt; building this pack in CI will roughly double ``update.yml``'s setup time,
which is why the cadence is quarterly and the job should be a separate
workflow_dispatch rather than part of the weekly run.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import util  # noqa: E402


def main() -> int:
    util.info(__doc__ or "")
    util.info("")
    util.fail(
        "build_topo.py is a TODO stub and builds nothing. The manifest entry "
        "maps-topo-us-md stays a placeholder until this is written (see README.md, "
        "Open questions).",
        code=2,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
