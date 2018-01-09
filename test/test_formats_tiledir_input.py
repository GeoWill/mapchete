"""Test Mapchete default formats."""

import pytest
import os
import yaml
from tilematrix import TilePyramid
from rasterio.crs import CRS
from mapchete.formats import available_input_formats
from mapchete.formats.default import tile_directory

import mapchete
from mapchete import errors


SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))
TESTDATA_DIR = os.path.join(SCRIPTDIR, "testdata")


def test_driver_available():
    """Driver is correctly registered."""
    assert "TileDirectory" in available_input_formats()


def test_parse_bounds(geojson_tiledir):
    """Read and configure bounds."""
    geojson_tiledir.dict["input"]["file1"].update(path=SCRIPTDIR)
    # fall back to pyramid bounds
    with mapchete.open(geojson_tiledir.dict) as mp:
        ip = mp.config.at_zoom(4)["input"]["file1"]
        assert ip.bbox().bounds == (-180, -90, 180, 90)
    # user defined bounds
    user_bounds = (0, 0, 30, 30)
    geojson_tiledir.dict["input"]["file1"].update(bounds=user_bounds)
    with mapchete.open(geojson_tiledir.dict) as mp:
        ip = mp.config.at_zoom(4)["input"]["file1"]
        assert ip.bbox().bounds == user_bounds
        # reproject
        assert ip.bbox(out_crs="3857")


def test_read_vector_data(mp_tmpdir, geojson, geojson_tiledir):
    """Read vector data."""
    # prepare data
    with mapchete.open(geojson.path) as mp:
        mp.batch_process(zoom=4)
    # read data
    features = []
    with mapchete.open(geojson_tiledir.path) as mp:
        for tile in mp.get_process_tiles(4):
            input_tile = mp.config.inputs.values()[0].open(tile)
            features.extend(input_tile.read())
    assert features


def test_read_raster_data():
    pass


def test_parse_errors():
    pass
