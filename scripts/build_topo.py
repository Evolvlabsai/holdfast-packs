#!/usr/bin/env python3
"""Build a per-state terrain pack: ONE PMTiles v3 archive of Terrarium elevation tiles.

    python scripts/build_topo.py --region us-md --out dist/us-md-topo.pmtiles
    python scripts/build_topo.py --region us-md --dry-run      # tile list + size estimate, no download
    python scripts/build_topo.py --region us-va --source 1     # 1 arc-second (~30 m) source cells

No GDAL, no tippecanoe. numpy + tifffile (+ imagecodecs for the LZW/deflate
GeoTIFFs) read the DEM, Pillow writes the PNGs, the ``pmtiles`` package writes
the archive. All of them are build-only dependencies (scripts/requirements.txt).

THE DECISION
------------
PMTiles holds one tile type per archive and a manifest pack has one URL, so the
pack ships **elevation only**, as raster-dem tiles. Contours and hillshade are
drawn on the phone from these tiles (MapLibre ``raster-dem`` source with
``encoding: terrarium`` gives hillshade directly; contours are generated on
device from the same tiles). One file, one URL, no second pack.

CONTRACT (the app is built against this -- do not change it casually)
--------
* ``dist/<region>-topo.pmtiles``, PMTiles v3, tile_type PNG, tile_compression
  none (PNG is already compressed).
* Web Mercator XYZ, 256x256, minzoom 5, maxzoom 12, bounds = the region bbox.
* Terrarium encoding: ``height_m = (R*256 + G + B/256) - 32768``.
  Sea and no-data are 0 m. Every tile intersecting the bbox is present, ocean
  included, so the map has no holes.
* Metadata JSON: name, ``"encoding": "terrarium"``, attribution
  ``USGS 3D Elevation Program (public domain)``, ``"vector_layers": []``.

INPUTS
------
USGS 3DEP 1/3 arc-second seamless DEM, 1x1 degree GeoTIFFs, public domain:

    https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n39w077/USGS_13_n39w077.tif

``--source 1`` uses the 1 arc-second (~30 m) product instead, same layout:

    https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1/TIFF/current/n39w077/USGS_1_n39w077.tif

3612x3612 cells of ~40-60 MB, about a ninth of the download. At maxzoom 12 a
pixel is already ~30 m, so the output is nearly the same; it needs no box
reduction (factor 1). The default stays ``13`` so Maryland rebuilds
byte-identically.

The tile name is the cell's NW corner: ``n{ceil(lat)}w{abs(floor(lon))}``.
Each is 10812x10812 float32 (10800 + a 6-pixel overlap on every side),
120-520 MB. The cells overlapping the region bbox are downloaded **plus one
ring of neighbouring cells** (``CELL_RING``), so an edge tile that reaches past
the bbox into the next 1x1 degree cell still has real elevation to its edges
instead of a 0 m strip. Maryland: 15 overlapping cells, 35 with the ring. The
ring changes only pixels outside the bbox's own cells, so tiles lying fully
inside the bbox are byte-identical with or without it. One ring covers every
tile at z9 and above (a z9 tile is ~0.7 degrees wide); z5-z8 tiles that reach
more than a degree past the bbox are still 0 m out there. Downloads use conditional GETs (``holdfast.httpcache``), into
``--cache-dir`` (default ``../holdfast-dist/topo-cache``, outside the repo so a
``git clean`` never throws away gigabytes). The bbox comes from the same region
file roads uses: ``packs/maps-roads-us-md/regions/<region>.json``.

STEPS
-----
1. Download the overlapping 3DEP cells plus one ring of neighbours (missing
   cells, e.g. open ocean, are 0 m).
2. Read each with tifffile; georeference from ModelTiepoint/ModelPixelScale;
   no-data -> 0; box-average by an integer factor to roughly the maxzoom pixel
   size (3x3 at z12, ~30 m), which is the anti-aliasing step. The reduced grid
   is cached as ``.npz`` next to the download.
3. maxzoom: for every tile intersecting the bbox, bilinear-sample the reduced
   grids at each pixel centre (inverse Mercator per row).
4. Each lower zoom: 2x2 mean of its four children. A child outside the bbox's
   tile range is sampled directly instead, so edge tiles are complete.
5. Encode Terrarium PNG, write all tiles in tile-id order (clustered archive).

OUTPUT
------
Then, as for every hosted pack:

    gh release upload maps-<yyyy.mm> dist/<region>-topo.pmtiles
    python scripts/update_manifest.py --id maps-topo-<region> \\
        --file dist/<region>-topo.pmtiles --url <release asset url> \\
        --changes "Rebuilt from the current USGS 3DEP release."
"""

from __future__ import annotations

import argparse
import concurrent.futures
import io
import json
import math
import sys
import urllib.error
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from holdfast import httpcache, util  # noqa: E402

#: 3DEP products, by the directory name USGS uses: "13" is 1/3 arc-second (~10 m),
#: "1" is 1 arc-second (~30 m), "2" is 2 arc-second (~60 m; Alaska only, the
#: statewide Alaska product). Same 1x1 degree cells, same NW-corner names.
DEM_URL_TEMPLATE = "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/{res}/TIFF/current/{name}/USGS_{res}_{name}.tif"
SOURCES = ("13", "1", "2")
DEFAULT_SOURCE = "13"
DEM_URL = DEM_URL_TEMPLATE.replace("{res}", DEFAULT_SOURCE)

#: Human label for the metadata description.
SOURCE_LABEL = {"13": "1/3 arc-second", "1": "1 arc-second", "2": "2 arc-second"}

TILE_SIZE = 256
MIN_ZOOM = 5
MAX_ZOOM = 12

#: Source pixel size in metres along a meridian (the coarser axis of the cell).
SOURCE_RES_M_BY_SOURCE = {
    "13": (1.0 / 3.0) / 3600.0 * 111_320.0,
    "1": 1.0 / 3600.0 * 111_320.0,
    "2": 2.0 / 3600.0 * 111_320.0,
}
SOURCE_RES_M = SOURCE_RES_M_BY_SOURCE[DEFAULT_SOURCE]

#: Anything below this is a no-data marker (3DEP uses -999999), not terrain.
NODATA_FLOOR = -10_000.0

ATTRIBUTION = "USGS 3D Elevation Program (public domain)"

#: Average PNG size per tile, for --dry-run (MD 2026-11 build: 205 MB / 1996 tiles).
EST_BYTES_PER_TILE = 103_000

RAW_DEPS_HINT = "Install the build-only deps: python -m pip install -r scripts/requirements.txt"


# --------------------------------------------------------------------------- tile math


def lon_to_tile_x(lon: float, z: int) -> float:
    return (lon + 180.0) / 360.0 * (1 << z)


def lat_to_tile_y(lat: float, z: int) -> float:
    lat = max(min(lat, 85.0511287798), -85.0511287798)
    rad = math.radians(lat)
    return (1.0 - math.asinh(math.tan(rad)) / math.pi) / 2.0 * (1 << z)


def tile_range(bbox: list[float] | tuple[float, ...], z: int) -> tuple[int, int, int, int]:
    """Inclusive (x0, y0, x1, y1) of the tiles at zoom ``z`` that intersect ``bbox``."""
    min_lon, min_lat, max_lon, max_lat = bbox
    n = 1 << z
    x0 = int(math.floor(lon_to_tile_x(min_lon, z)))
    x1 = int(math.floor(lon_to_tile_x(max_lon, z)))
    y0 = int(math.floor(lat_to_tile_y(max_lat, z)))
    y1 = int(math.floor(lat_to_tile_y(min_lat, z)))
    clamp = lambda v: max(0, min(n - 1, v))  # noqa: E731
    return clamp(x0), clamp(y0), clamp(x1), clamp(y1)


def tiles_for_bbox(bbox, z: int) -> list[tuple[int, int, int]]:
    x0, y0, x1, y1 = tile_range(bbox, z)
    return [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]


def pixel_lonlat(z: int, x: int, y: int, size: int = TILE_SIZE) -> tuple[np.ndarray, np.ndarray]:
    """Longitudes (per column) and latitudes (per row) of the pixel centres of a tile."""
    world = float(size << z)
    px = (x * size + np.arange(size) + 0.5) / world
    py = (y * size + np.arange(size) + 0.5) / world
    lons = px * 360.0 - 180.0
    lats = np.degrees(np.arctan(np.sinh(np.pi * (1.0 - 2.0 * py))))
    return lons, lats


# --------------------------------------------------------------------------- 3DEP naming


def dem_cell_name(south: int, west: int) -> str:
    """Name of the 1x1 degree cell whose SW corner is (south, west): its NW corner."""
    north = south + 1
    lat = f"n{north:02d}" if north >= 0 else f"s{-north:02d}"
    lon = f"w{-west:03d}" if west < 0 else f"e{west:03d}"
    return lat + lon


def dem_name_for_point(lat: float, lon: float) -> str:
    """``n{ceil(lat)}w{abs(floor(lon))}`` -- the cell containing the point."""
    return dem_cell_name(math.floor(lat), math.floor(lon))


def dem_url(name: str, source: str = DEFAULT_SOURCE) -> str:
    """Download URL of one 3DEP cell for ``source`` ("13" or "1")."""
    if source not in SOURCES:
        raise ValueError(f"unknown 3DEP source {source!r}; expected one of {SOURCES}")
    return DEM_URL_TEMPLATE.format(res=source, name=name)


def dem_filename(name: str, source: str = DEFAULT_SOURCE) -> str:
    """Local cache file name, as USGS names it: ``USGS_13_n39w077.tif`` / ``USGS_1_n39w077.tif``."""
    if source not in SOURCES:
        raise ValueError(f"unknown 3DEP source {source!r}; expected one of {SOURCES}")
    return f"USGS_{source}_{name}.tif"


#: Extra rings of 1x1 degree cells fetched around the bbox, so edge tiles are not cut off at 0 m.
CELL_RING = 1


def dem_cells_with_ring(bbox, ring: int = CELL_RING) -> list[tuple[int, int]]:
    """The cells overlapping ``bbox`` plus ``ring`` rings of neighbours.

    Clamped to +-90 latitude and +-180 longitude: a bbox that stops at the
    antimeridian (Alaska's, at -180) gets no ring past it, since there are no
    cells named w181 and the archive does not wrap.
    """
    min_lon, min_lat, max_lon, max_lat = bbox
    grown = [
        max(-180.0, min_lon - ring),
        max(-90.0, min_lat - ring),
        min(180.0, max_lon + ring),
        min(90.0, max_lat + ring),
    ]
    return dem_cells_for_bbox(grown)


def dem_cells_for_bbox(bbox) -> list[tuple[int, int]]:
    """(south, west) integer corners of every 1x1 degree cell overlapping ``bbox``."""
    min_lon, min_lat, max_lon, max_lat = bbox
    return [
        (s, w)
        for s in range(math.floor(min_lat), math.ceil(max_lat))
        for w in range(math.floor(min_lon), math.ceil(max_lon))
    ]


# --------------------------------------------------------------------------- Terrarium


def encode_terrarium(height: np.ndarray) -> np.ndarray:
    """Float metres (H, W) -> uint8 RGB (H, W, 3). NaN -> 0 m. Step is 1/256 m."""
    h = np.nan_to_num(np.asarray(height, dtype=np.float64), nan=0.0)
    q = np.round((np.clip(h, -32768.0, 32767.0) + 32768.0) * 256.0).astype(np.int64)
    q = np.clip(q, 0, (1 << 24) - 1)
    rgb = np.empty(h.shape + (3,), dtype=np.uint8)
    rgb[..., 0] = q >> 16
    rgb[..., 1] = (q >> 8) & 0xFF
    rgb[..., 2] = q & 0xFF
    return rgb


def decode_terrarium(rgb: np.ndarray) -> np.ndarray:
    rgb = np.asarray(rgb, dtype=np.float64)
    return rgb[..., 0] * 256.0 + rgb[..., 1] + rgb[..., 2] / 256.0 - 32768.0


def downsample2(mosaic: np.ndarray) -> np.ndarray:
    """2x2 mean: (2H, 2W) -> (H, W)."""
    h, w = mosaic.shape
    return mosaic.reshape(h // 2, 2, w // 2, 2).mean(axis=(1, 3), dtype=np.float64).astype(np.float32)


def box_reduce(arr: np.ndarray, factor: int) -> np.ndarray:
    """Block mean by an integer ``factor``, trimming the ragged edge."""
    if factor <= 1:
        return arr.astype(np.float32, copy=False)
    h = arr.shape[0] // factor * factor
    w = arr.shape[1] // factor * factor
    out = np.zeros((h // factor, w // factor), dtype=np.float64)
    for i in range(factor):
        for j in range(factor):
            out += arr[i:h:factor, j:w:factor]
    return (out / (factor * factor)).astype(np.float32)


def reduce_factor(maxzoom: int, lat: float, source: str = DEFAULT_SOURCE) -> int:
    """Integer box factor taking source pixels to about the maxzoom pixel size."""
    target = 40_075_016.686 * math.cos(math.radians(lat)) / (TILE_SIZE << maxzoom)
    return max(1, round(target / SOURCE_RES_M_BY_SOURCE[source]))


# --------------------------------------------------------------------------- DEM grids


@dataclass
class Dem:
    """A georeferenced elevation grid in geographic coordinates."""

    data: np.ndarray  # (H, W) float32, metres, no-data already 0
    west: float  # lon of the left edge of column 0
    north: float  # lat of the top edge of row 0
    dx: float  # degrees per column
    dy: float  # degrees per row (positive)

    def sample(self, lons: np.ndarray, lats: np.ndarray) -> np.ndarray:
        """Bilinear sample at paired 1-D arrays of points."""
        h, w = self.data.shape
        col = np.clip((lons - self.west) / self.dx - 0.5, 0.0, w - 1.0)
        row = np.clip((self.north - lats) / self.dy - 0.5, 0.0, h - 1.0)
        c0 = np.minimum(col.astype(np.int64), w - 2)
        r0 = np.minimum(row.astype(np.int64), h - 2)
        fc = col - c0
        fr = row - r0
        d = self.data
        top = d[r0, c0] * (1 - fc) + d[r0, c0 + 1] * fc
        bot = d[r0 + 1, c0] * (1 - fc) + d[r0 + 1, c0 + 1] * fc
        return top * (1 - fr) + bot * fr


def read_geotiff(path: Path) -> Dem:
    """Read a north-up float GeoTIFF with tifffile. Data files only: no GDAL, no code."""
    try:
        import tifffile
    except ImportError:
        util.fail(f"tifffile is not installed. {RAW_DEPS_HINT}")

    with tifffile.TiffFile(path) as tif:
        page = tif.pages[0]
        tags = page.tags
        tie = tags.get("ModelTiepointTag")
        scale = tags.get("ModelPixelScaleTag")
        if tie is None or scale is None:
            util.fail(f"{path}: no ModelTiepoint/ModelPixelScale tags; not a north-up GeoTIFF")
        i, j, _k, x, y, _z = tie.value[:6]
        sx, sy = scale.value[:2]
        nodata_tag = tags.get("GDAL_NODATA")
        nodata = None
        if nodata_tag is not None:
            try:
                nodata = float(str(nodata_tag.value).strip("\x00 "))
            except ValueError:
                nodata = None
        data = page.asarray().astype(np.float32, copy=False)

    bad = ~np.isfinite(data) | (data < NODATA_FLOOR)
    if nodata is not None:
        bad |= data == nodata
    data[bad] = 0.0
    return Dem(data=data, west=x - i * sx, north=y + j * sy, dx=sx, dy=sy)


def load_reduced(tif: Path, factor: int) -> Dem:
    """The DEM box-reduced by ``factor``, cached as ``<name>.f<factor>.npz`` next to it."""
    npz = tif.with_name(f"{tif.stem}.f{factor}.npz")
    stamp = f"{tif.stat().st_size}:{int(tif.stat().st_mtime)}"
    if npz.exists():
        with np.load(npz) as z:
            if str(z["stamp"]) == stamp:
                west, north, dx, dy = (float(v) for v in z["transform"])
                return Dem(z["data"], west, north, dx, dy)
    full = read_geotiff(tif)
    reduced = Dem(box_reduce(full.data, factor), full.west, full.north, full.dx * factor, full.dy * factor)
    del full
    tmp = npz.with_suffix(".tmp.npz")
    np.savez(tmp, data=reduced.data, transform=np.array([reduced.west, reduced.north, reduced.dx, reduced.dy]), stamp=np.array(stamp))
    tmp.replace(npz)
    return reduced


class Mosaic:
    """1x1 degree DEM cells keyed by integer (south, west); a missing cell is 0 m."""

    def __init__(self, cells: dict[tuple[int, int], Dem | None]):
        self.cells = cells

    def sample_tile(self, z: int, x: int, y: int) -> np.ndarray:
        lons, lats = pixel_lonlat(z, x, y)
        lon_grid = np.broadcast_to(lons[None, :], (TILE_SIZE, TILE_SIZE))
        lat_grid = np.broadcast_to(lats[:, None], (TILE_SIZE, TILE_SIZE))
        out = np.zeros((TILE_SIZE, TILE_SIZE), dtype=np.float32)
        south = np.floor(lat_grid).astype(np.int64)
        west = np.floor(lon_grid).astype(np.int64)
        for s in np.unique(south):
            for w in np.unique(west):
                dem = self.cells.get((int(s), int(w)))
                if dem is None:
                    continue
                mask = (south == s) & (west == w)
                if mask.any():
                    out[mask] = dem.sample(lon_grid[mask], lat_grid[mask])
        return out


# --------------------------------------------------------------------------- build


def png_bytes(height: np.ndarray) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.fromarray(encode_terrarium(height), mode="RGB").save(buf, format="PNG", compress_level=9)
    return buf.getvalue()


def build_tiles(mosaic: Mosaic, bbox, minzoom: int, maxzoom: int, log=util.info) -> dict[tuple[int, int, int], bytes]:
    """Every tile in the bbox for minzoom..maxzoom, as Terrarium PNG bytes."""
    out: dict[tuple[int, int, int], bytes] = {}
    level: dict[tuple[int, int], np.ndarray] = {}
    started = time.monotonic()

    tiles = tiles_for_bbox(bbox, maxzoom)
    with concurrent.futures.ThreadPoolExecutor() as pool:
        for (z, x, y), arr in zip(tiles, pool.map(lambda t: mosaic.sample_tile(*t), tiles), strict=True):
            level[(x, y)] = arr
        for (z, x, y), png in zip(tiles, pool.map(lambda t: png_bytes(level[t[1:]]), tiles), strict=True):
            out[(z, x, y)] = png
    log(f"  z{maxzoom}: {len(tiles)} tiles ({time.monotonic() - started:.0f}s)")

    for z in range(maxzoom - 1, minzoom - 1, -1):
        tiles = tiles_for_bbox(bbox, z)
        parent_level: dict[tuple[int, int], np.ndarray] = {}
        for _, x, y in tiles:
            mosaic_arr = np.empty((TILE_SIZE * 2, TILE_SIZE * 2), dtype=np.float32)
            for dy in (0, 1):
                for dx in (0, 1):
                    cx, cy = 2 * x + dx, 2 * y + dy
                    child = level.get((cx, cy))
                    if child is None:
                        child = mosaic.sample_tile(z + 1, cx, cy)
                    mosaic_arr[dy * TILE_SIZE:(dy + 1) * TILE_SIZE, dx * TILE_SIZE:(dx + 1) * TILE_SIZE] = child
            parent_level[(x, y)] = downsample2(mosaic_arr)
        with concurrent.futures.ThreadPoolExecutor() as pool:
            for (zz, x, y), png in zip(tiles, pool.map(lambda t: png_bytes(parent_level[t[1:]]), tiles), strict=True):
                out[(zz, x, y)] = png
        level = parent_level
        log(f"  z{z}: {len(tiles)} tiles ({time.monotonic() - started:.0f}s)")
    return out


def write_pmtiles(
    path: Path, tiles: dict[tuple[int, int, int], bytes], bbox, region_name: str, source: str = DEFAULT_SOURCE
) -> None:
    from pmtiles.tile import Compression, TileType, zxy_to_tileid
    from pmtiles.writer import write

    min_lon, min_lat, max_lon, max_lat = bbox
    zooms = sorted({z for z, _, _ in tiles})
    ordered = sorted(tiles.items(), key=lambda kv: zxy_to_tileid(*kv[0]))
    e7 = lambda v: int(round(v * 10_000_000))  # noqa: E731
    header = {
        "tile_type": TileType.PNG,
        "tile_compression": Compression.NONE,
        "min_zoom": zooms[0],
        "max_zoom": zooms[-1],
        "min_lon_e7": e7(min_lon),
        "min_lat_e7": e7(min_lat),
        "max_lon_e7": e7(max_lon),
        "max_lat_e7": e7(max_lat),
        "center_zoom": min(max(zooms[0], 8), zooms[-1]),
        "center_lon_e7": e7((min_lon + max_lon) / 2),
        "center_lat_e7": e7((min_lat + max_lat) / 2),
    }
    metadata = {
        "name": f"{region_name} terrain",
        "encoding": "terrarium",
        "attribution": ATTRIBUTION,
        "vector_layers": [],
        "type": "baselayer",
        "format": "png",
        "description": f"USGS 3DEP {SOURCE_LABEL[source]} DEM as Terrarium raster-dem tiles: "
        "height_m = (R*256 + G + B/256) - 32768; sea and no-data are 0 m.",
        "minzoom": zooms[0],
        "maxzoom": zooms[-1],
        "bounds": [min_lon, min_lat, max_lon, max_lat],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    with write(str(tmp)) as writer:
        for (z, x, y), data in ordered:
            writer.write_tile(zxy_to_tileid(z, x, y), data)
        writer.finalize(header, metadata)
    tmp.replace(path)


def fetch_cells(
    cells: list[tuple[int, int]], cache_dir: Path, source: str = DEFAULT_SOURCE
) -> dict[tuple[int, int], Path | None]:
    """Download (conditionally) every cell; None for a cell 3DEP does not publish."""
    cache = httpcache.Cache.load(cache_dir / "http.json")
    result: dict[tuple[int, int], Path | None] = {}

    def one(cell: tuple[int, int]) -> tuple[tuple[int, int], Path | None, str]:
        name = dem_cell_name(*cell)
        url = dem_url(name, source)
        dest = cache_dir / dem_filename(name, source)
        try:
            wrote = httpcache.download(url, dest, cache=cache, timeout=120)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404):
                return cell, None, f"{name}: not published (HTTP {exc.code}); treated as 0 m"
            raise
        return cell, dest, f"{name}: {'downloaded' if wrote else 'cached'} ({util.human_bytes(dest.stat().st_size)})"

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for cell, path, message in pool.map(one, cells):
            util.info(f"  {message}")
            result[cell] = path
    cache.save()
    return result


def load_region(root: Path, region_id: str) -> dict:
    path = root / "packs" / "maps-roads-us-md" / "regions" / f"{region_id}.json"
    if not path.exists():
        util.fail(f"no region file {path}")
    region = json.loads(path.read_text(encoding="utf-8"))
    bbox = region.get("bbox")
    if not (isinstance(bbox, list) and len(bbox) == 4):
        util.fail(f"{path}: bbox must be [min_lon, min_lat, max_lon, max_lat]")
    return region


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--region", required=True, help="region id, e.g. us-md (packs/maps-roads-us-md/regions/us-md.json)")
    parser.add_argument("--out", default=None, help="output .pmtiles (default: dist/<region>-topo.pmtiles)")
    parser.add_argument("--maxzoom", type=int, default=MAX_ZOOM, help=f"max zoom (default: {MAX_ZOOM})")
    parser.add_argument("--minzoom", type=int, default=MIN_ZOOM, help=f"min zoom (default: {MIN_ZOOM})")
    parser.add_argument(
        "--cache-dir",
        default=None,
        help="where the 3DEP GeoTIFFs are kept (default: ../holdfast-dist/topo-cache next to the repo)",
    )
    parser.add_argument(
        "--source",
        choices=SOURCES,
        default=DEFAULT_SOURCE,
        help='3DEP product: "13" = 1/3 arc-second (~10 m, default), "1" = 1 arc-second (~30 m, ~9x less download), '
        '"2" = 2 arc-second (~60 m, Alaska only)',
    )
    parser.add_argument("--dry-run", action="store_true", help="print the DEM cells and tile counts, estimate size, download nothing")
    args = parser.parse_args(argv)

    if not 0 <= args.minzoom <= args.maxzoom <= 16:
        util.fail("need 0 <= --minzoom <= --maxzoom <= 16")

    root = util.repo_root()
    region = load_region(root, args.region)
    bbox = [float(v) for v in region["bbox"]]
    name = region.get("name", region["id"])
    out = Path(args.out) if args.out else root / "dist" / f"{region['id']}-topo.pmtiles"
    cache_dir = Path(args.cache_dir) if args.cache_dir else root.parent / "holdfast-dist" / "topo-cache"

    cells = dem_cells_with_ring(bbox)
    counts = {z: len(tiles_for_bbox(bbox, z)) for z in range(args.minzoom, args.maxzoom + 1)}
    total = sum(counts.values())
    util.info(f"region {region['id']} ({name}), bbox {bbox}")
    util.info(f"tiles: {total} (" + ", ".join(f"z{z} {n}" for z, n in counts.items()) + ")")
    util.info(f"3DEP cells: {len(cells)} ({SOURCE_LABEL[args.source]})")

    if args.dry_run:
        source_bytes = 0
        for cell in cells:
            cell_name = dem_cell_name(*cell)
            head = httpcache.head(dem_url(cell_name, args.source))
            size = head.length if head.ok else None
            source_bytes += size or 0
            status = util.human_bytes(size) if head.ok else f"missing ({head.error})"
            util.info(f"  {cell_name}: {status}")
        util.info(f"download: ~{util.human_bytes(source_bytes)} (cached copies are revalidated, not refetched)")
        util.info("tile list (inclusive x and y ranges; every tile in the rectangle is built):")
        for z in counts:
            x0, y0, x1, y1 = tile_range(bbox, z)
            util.info(f"  z{z}: x {x0}..{x1}, y {y0}..{y1} -> {counts[z]} tiles")
        util.info(f"estimated output: ~{util.human_bytes(total * EST_BYTES_PER_TILE)}")
        return 0

    try:
        import pmtiles  # noqa: F401
        import PIL  # noqa: F401
        import tifffile  # noqa: F401
    except ImportError as exc:
        util.fail(f"{exc}. {RAW_DEPS_HINT}")

    started = time.monotonic()
    util.info(f"downloading into {cache_dir}")
    paths = fetch_cells(cells, cache_dir, args.source)

    factor = reduce_factor(args.maxzoom, (bbox[1] + bbox[3]) / 2, args.source)
    util.info(f"reading DEMs, box factor {factor}")
    dems: dict[tuple[int, int], Dem | None] = {}
    for cell, path in paths.items():
        dems[cell] = load_reduced(path, factor) if path else None
    mosaic = Mosaic(dems)

    util.info("rendering tiles")
    tiles = build_tiles(mosaic, bbox, args.minzoom, args.maxzoom)
    write_pmtiles(out, tiles, bbox, name, args.source)

    size, sha = util.size_and_sha256(out)
    util.info("")
    util.info(f"built {out}")
    util.info(f"  tiles  {len(tiles)} (" + ", ".join(f"z{z} {n}" for z, n in counts.items()) + ")")
    util.info(f"  size   {size} bytes ({util.human_bytes(size)})")
    util.info(f"  sha256 {sha}")
    util.info(f"  time   {time.monotonic() - started:.0f}s")
    util.info("")
    util.info("next: upload it to the maps release and run update_manifest.py (see the docstring).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
