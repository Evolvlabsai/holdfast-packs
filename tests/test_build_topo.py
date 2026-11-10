"""build_topo.py: the pure parts (Terrarium, tile math, 3DEP naming). No network."""

from __future__ import annotations

import io
import math

import numpy as np
import pytest

import build_topo as bt

MD_BBOX = [-79.49, 37.88, -75.05, 39.73]


# --------------------------------------------------------------------------- Terrarium


def test_terrarium_round_trip_is_within_one_step():
    heights = np.array([[-32768.0, -432.1, -0.5, 0.0], [0.004, 12.34, 1024.0, 8848.86]])
    decoded = bt.decode_terrarium(bt.encode_terrarium(heights))
    assert np.max(np.abs(decoded - heights)) <= 1 / 512 + 1e-9


def test_terrarium_zero_is_the_documented_rgb():
    # (128*256 + 0 + 0/256) - 32768 = 0
    assert bt.encode_terrarium(np.zeros((1, 1)))[0, 0].tolist() == [128, 0, 0]


def test_terrarium_matches_the_contract_formula():
    rgb = bt.encode_terrarium(np.array([[1000.25]]))[0, 0].astype(int)
    r, g, b = rgb.tolist()
    assert (r * 256 + g + b / 256) - 32768 == pytest.approx(1000.25)


def test_terrarium_nan_is_sea_level():
    assert bt.decode_terrarium(bt.encode_terrarium(np.array([[np.nan]])))[0, 0] == 0.0


def test_png_bytes_decode_back_to_heights():
    from PIL import Image

    heights = np.linspace(-10, 1100, 256 * 256, dtype=np.float32).reshape(256, 256)
    img = Image.open(io.BytesIO(bt.png_bytes(heights)))
    assert img.mode == "RGB" and img.size == (256, 256)
    assert np.max(np.abs(bt.decode_terrarium(np.asarray(img)) - heights)) < 0.01


def test_downsample2_is_a_2x2_mean():
    a = np.arange(16, dtype=np.float32).reshape(4, 4)
    assert bt.downsample2(a).tolist() == [[2.5, 4.5], [10.5, 12.5]]


def test_box_reduce_trims_and_averages():
    a = np.ones((7, 7), dtype=np.float32)
    a[:3, :3] = 4
    out = bt.box_reduce(a, 3)
    assert out.shape == (2, 2)
    assert out[0, 0] == 4 and out[1, 1] == 1


def test_reduce_factor_is_about_30m_at_z12_in_maryland():
    assert bt.reduce_factor(12, 38.8) == 3
    assert bt.reduce_factor(14, 38.8) == 1


# --------------------------------------------------------------------------- tile math


def test_md_tile_counts_per_zoom():
    counts = {z: len(bt.tiles_for_bbox(MD_BBOX, z)) for z in range(5, 13)}
    assert counts == {5: 2, 6: 2, 7: 6, 8: 8, 9: 32, 10: 112, 11: 378, 12: 1456}


def test_tile_range_covers_the_bbox_corners():
    for z in range(5, 13):
        x0, y0, x1, y1 = bt.tile_range(MD_BBOX, z)
        assert x0 == math.floor(bt.lon_to_tile_x(-79.49, z))
        assert x1 == math.floor(bt.lon_to_tile_x(-75.05, z))
        assert y0 == math.floor(bt.lat_to_tile_y(39.73, z))  # north edge -> smallest y
        assert y1 == math.floor(bt.lat_to_tile_y(37.88, z))


def test_known_tile_for_annapolis_at_z12():
    # Standard slippy-map formula (ln(tan + sec)): 38.98N 76.49W -> 12/1177/1565.
    assert int(bt.lon_to_tile_x(-76.49, 12)) == 1177
    assert int(bt.lat_to_tile_y(38.98, 12)) == 1565


def test_pixel_lonlat_stays_inside_its_tile():
    z, x, y = 12, 1177, 1567
    lons, lats = bt.pixel_lonlat(z, x, y)
    assert lons.shape == lats.shape == (256,)
    assert np.all(np.diff(lons) > 0) and np.all(np.diff(lats) < 0)  # west->east, north->south
    assert x <= bt.lon_to_tile_x(lons[0], z) < bt.lon_to_tile_x(lons[-1], z) < x + 1
    assert y <= bt.lat_to_tile_y(lats[0], z) < bt.lat_to_tile_y(lats[-1], z) < y + 1


# --------------------------------------------------------------------------- 3DEP naming


@pytest.mark.parametrize(
    ("lat", "lon", "name"),
    [
        (38.98, -76.49, "n39w077"),  # Annapolis
        (39.237, -79.486, "n40w080"),  # Hoye-Crest
        (37.88, -75.05, "n38w076"),
        (38.0, -77.0, "n39w077"),  # on a corner: the cell to its NE
    ],
)
def test_nw_corner_naming(lat, lon, name):
    assert bt.dem_name_for_point(lat, lon) == name


def test_md_needs_fifteen_cells():
    names = sorted(bt.dem_cell_name(s, w) for s, w in bt.dem_cells_for_bbox(MD_BBOX))
    assert len(names) == 15
    assert names[0] == "n38w076" and names[-1] == "n40w080"
    assert "n39w077" in names and "n38w075" not in names


def test_dem_url_scheme():
    assert bt.DEM_URL.format(name="n39w077") == (
        "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/current/n39w077/USGS_13_n39w077.tif"
    )


# --------------------------------------------------------------------------- sampling + archive


def _ramp_cell(south: int, west: int, n: int = 61) -> bt.Dem:
    """A synthetic 1x1 degree cell whose height is 1000 * (lon - west)."""
    dx = 1.0 / (n - 1)
    lons = west + (np.arange(n) + 0.5) * dx - dx / 2
    data = np.tile((lons - west) * 1000.0, (n, 1)).astype(np.float32)
    return bt.Dem(data=data, west=west - dx / 2, north=south + 1 + dx / 2, dx=dx, dy=dx)


def test_mosaic_samples_and_missing_cells_are_zero():
    mosaic = bt.Mosaic({(38, -77): _ramp_cell(38, -77), (38, -76): None})
    z, x, y = 12, int(bt.lon_to_tile_x(-76.5, 12)), int(bt.lat_to_tile_y(38.5, 12))
    tile = mosaic.sample_tile(z, x, y)
    lons, _ = bt.pixel_lonlat(z, x, y)
    assert np.allclose(tile[128], (lons + 77) * 1000.0, atol=0.5)
    far = mosaic.sample_tile(z, int(bt.lon_to_tile_x(-75.5, 12)), y)
    assert not far.any()


def test_write_pmtiles_header_and_metadata(tmp_path):
    from pmtiles.reader import MmapSource, Reader
    from pmtiles.tile import Compression, TileType

    sea = bt.png_bytes(np.zeros((256, 256), dtype=np.float32))
    tiles = {(z, x, y): sea for z in (5, 6) for z_, x, y in bt.tiles_for_bbox(MD_BBOX, z) if z_ == z}
    out = tmp_path / "t.pmtiles"
    bt.write_pmtiles(out, tiles, MD_BBOX, "Maryland")
    with open(out, "rb") as fh:
        reader = Reader(MmapSource(fh))
        header = reader.header()
        meta = reader.metadata()
        assert header["tile_type"] == TileType.PNG
        assert header["tile_compression"] == Compression.NONE
        assert (header["min_zoom"], header["max_zoom"]) == (5, 6)
        assert header["min_lon_e7"] == -794_900_000 and header["max_lat_e7"] == 397_300_000
        assert meta["name"] == "Maryland terrain"
        assert meta["encoding"] == "terrarium"
        assert meta["attribution"] == "USGS 3D Elevation Program (public domain)"
        assert meta["vector_layers"] == []
        z, x, y = bt.tiles_for_bbox(MD_BBOX, 6)[0]
        assert reader.get(z, x, y) == sea


# --------------------------------------------------------------------------- --source


def test_default_source_is_one_third_arc_second():
    assert bt.DEFAULT_SOURCE == "13"
    assert bt.dem_url("n39w077") == bt.DEM_URL.format(name="n39w077")
    assert bt.dem_filename("n39w077") == "USGS_13_n39w077.tif"
    assert bt.SOURCE_RES_M == bt.SOURCE_RES_M_BY_SOURCE["13"]


def test_source_1_url_and_file_naming():
    assert bt.dem_url("n37w082", "1") == (
        "https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1/TIFF/current/n37w082/USGS_1_n37w082.tif"
    )
    assert bt.dem_filename("n37w082", "1") == "USGS_1_n37w082.tif"
    # The 1/3 arc-second cache file is never reused for a 1 arc-second build.
    assert bt.dem_filename("n39w077", "1") != bt.dem_filename("n39w077", "13")


def test_unknown_source_is_rejected():
    with pytest.raises(ValueError):
        bt.dem_url("n39w077", "2")
    with pytest.raises(ValueError):
        bt.dem_filename("n39w077", "1m")


def test_source_1_needs_no_box_reduction_at_z12():
    assert bt.reduce_factor(12, 38.8, "13") == 3
    assert bt.reduce_factor(12, 38.8, "1") == 1
    assert bt.reduce_factor(12, 41.0, "1") == 1  # Pennsylvania
    assert bt.reduce_factor(10, 38.8, "1") == 4


def test_dry_run_heads_the_chosen_source(monkeypatch):
    """--dry-run HEADs one URL per cell: 1/3" by default, 1" with --source 1."""
    from types import SimpleNamespace

    urls: list[str] = []

    def fake_head(url, *a, **k):
        urls.append(url)
        return SimpleNamespace(ok=True, length=1, error=None)

    monkeypatch.setattr(bt.httpcache, "head", fake_head)
    assert bt.main(["--region", "us-md", "--dry-run"]) == 0
    assert len(urls) == 15 and all("/Elevation/13/" in u and "/USGS_13_" in u for u in urls)
    urls.clear()
    assert bt.main(["--region", "us-md", "--dry-run", "--source", "1"]) == 0
    assert len(urls) == 15 and all("/Elevation/1/" in u and "/USGS_1_" in u for u in urls)
    with pytest.raises(SystemExit) as exc:
        bt.main(["--region", "us-md", "--source", "10"])
    assert exc.value.code == 2  # argparse: invalid choice


def test_metadata_names_the_source(tmp_path):
    from pmtiles.reader import MmapSource, Reader

    sea = bt.png_bytes(np.zeros((256, 256), dtype=np.float32))
    tiles = {t: sea for t in bt.tiles_for_bbox(MD_BBOX, 5)}
    for source, label in (("13", "USGS 3DEP 1/3 arc-second DEM"), ("1", "USGS 3DEP 1 arc-second DEM")):
        out = tmp_path / f"{source}.pmtiles"
        bt.write_pmtiles(out, tiles, MD_BBOX, "Maryland", source)
        with open(out, "rb") as fh:
            assert Reader(MmapSource(fh)).metadata()["description"].startswith(label + " as Terrarium")


def test_default_write_is_byte_identical_to_explicit_13(tmp_path):
    sea = bt.png_bytes(np.zeros((256, 256), dtype=np.float32))
    tiles = {t: sea for t in bt.tiles_for_bbox(MD_BBOX, 5)}
    a, b = tmp_path / "a.pmtiles", tmp_path / "b.pmtiles"
    bt.write_pmtiles(a, tiles, MD_BBOX, "Maryland")
    bt.write_pmtiles(b, tiles, MD_BBOX, "Maryland", "13")
    assert a.read_bytes() == b.read_bytes()
