"""Test Mapchete default formats."""

import datetime

import pytest
from rasterio.crs import CRS
from tilematrix import TilePyramid

import mapchete
from mapchete import errors
from mapchete.formats import (
    available_input_formats,
    available_output_formats,
    base,
    driver_from_extension,
    driver_from_file,
    dump_metadata,
    load_input_reader,
    load_metadata,
    load_output_reader,
    load_output_writer,
    read_output_metadata,
)
from mapchete.tile import BufferedTilePyramid


def test_available_input_formats():
    """Check if default input formats can be listed."""
    assert set(["Mapchete", "raster_file", "vector_file"]).issubset(
        set(available_input_formats())
    )


def test_available_output_formats():
    """Check if default output formats can be listed."""
    assert set(["GTiff", "PNG", "PNG_hillshade", "GeoJSON"]).issubset(
        set(available_output_formats())
    )


def test_output_writer_errors():
    """Test errors when loading output writer."""
    with pytest.raises(TypeError):
        load_output_writer("not_a_dictionary")
    with pytest.raises(errors.MapcheteDriverError):
        load_output_writer({"format": "invalid_driver"})


def test_output_reader_errors():
    """Test errors when loading output writer."""
    with pytest.raises(TypeError):
        load_output_reader("not_a_dictionary")
    with pytest.raises(errors.MapcheteDriverError):
        load_output_reader({"format": "invalid_driver"})


def test_input_reader_errors():
    """Test errors when loading input readers."""
    with pytest.raises(TypeError):
        load_input_reader("not_a_dictionary")
    with pytest.raises(errors.MapcheteDriverError):
        load_input_reader({})
    with pytest.raises(errors.MapcheteDriverError):
        load_input_reader({"abstract": {"format": "invalid_format"}})


def test_driver_from_file_tif():
    assert driver_from_file("some.tif") == "raster_file"


def test_driver_from_file_jp2():
    assert driver_from_file("some.jp2") == "raster_file"


def test_driver_from_file_geojson():
    assert driver_from_file("some.geojson") == "vector_file"


def test_driver_from_file_shp():
    assert driver_from_file("some.shp") == "vector_file"


def test_driver_from_file_mapchete():
    assert driver_from_file("some.mapchete") == "Mapchete"


def test_driver_from_file_errors(execute_kwargs_py):
    """Test errors when determining input driver from filename."""
    with pytest.raises(errors.MapcheteDriverError):
        driver_from_file(execute_kwargs_py)

    with pytest.raises(FileNotFoundError):
        driver_from_file("non_existing_file.tif", quick=False)


def test_mapchete_input(mapchete_input):
    """Mapchete process as input for other process."""
    with mapchete.open(mapchete_input.dict) as mp:
        config = mp.config.params_at_zoom(5)
        input_data = config["input"]["file2"]
        assert input_data.bbox()
        assert input_data.bbox(CRS.from_epsg(3857))
        mp_input = input_data.open(next(mp.get_process_tiles(5)))
        assert not mp_input.is_empty()


def test_base_format_classes():
    """Base format classes."""
    # InputData
    tp = TilePyramid("geodetic")
    tmp = base.InputData(dict(pyramid=tp, pixelbuffer=0))
    assert tmp.pyramid
    assert tmp.pixelbuffer == 0
    assert tmp.crs
    with pytest.raises(NotImplementedError):
        tmp.open(None)
    with pytest.raises(NotImplementedError):
        tmp.bbox()
    with pytest.raises(NotImplementedError):
        tmp.exists()

    # InputTile
    tmp = base.InputTile(None)
    with pytest.raises(NotImplementedError):
        tmp.read()
    with pytest.raises(NotImplementedError):
        tmp.is_empty()

    # OutputDataWriter
    tmp = base.OutputDataWriter(dict(pixelbuffer=0, grid="geodetic", metatiling=1))
    assert tmp.pyramid
    assert tmp.pixelbuffer == 0
    assert tmp.crs
    with pytest.raises(NotImplementedError):
        tmp.read(None)
    with pytest.raises(NotImplementedError):
        tmp.write(None, None)
    with pytest.raises(NotImplementedError):
        tmp.is_valid_with_config(None)
    with pytest.raises(NotImplementedError):
        tmp.for_web(None)
    with pytest.raises(NotImplementedError):
        tmp.empty(None)
    with pytest.raises(NotImplementedError):
        tmp.open(None, None)


@pytest.mark.remote
def test_http_rasters(files_bounds, http_raster):
    """Raster file on remote server with http:// or https:// URLs."""
    zoom = 13
    config = files_bounds.dict
    config.update(input=dict(file1=http_raster), zoom_levels=zoom)
    # TODO make tests more performant
    with mapchete.open(config) as mp:
        assert mp.config.area_at_zoom(zoom).area > 0
        tile = next(mp.get_process_tiles(13))
        user_process = mapchete.MapcheteProcess(
            tile=tile,
            params=mp.config.params_at_zoom(tile.zoom),
            input=mp.config.get_inputs_for_tile(tile),
        )
        with user_process.open("file1") as f:
            assert f.read().any()


def test_read_from_raster_file(cleantopo_br):
    """Read different bands from source raster."""
    with mapchete.open(cleantopo_br.dict) as mp:
        tile = mp.config.process_pyramid.tile(5, 0, 0)
        user_process = mapchete.MapcheteProcess(
            tile=tile,
            params=mp.config.params_at_zoom(tile.zoom),
            input=mp.config.get_inputs_for_tile(tile),
        )
        with user_process.open("file1") as f:
            assert f.read().shape == f.read([1]).shape == (1, *f.read(1).shape)


def test_invalid_input_type(example_mapchete):
    """Raise MapcheteDriverError."""
    # invalid input type
    config = example_mapchete.dict
    config.update(input=dict(invalid_type=1))
    with pytest.raises(errors.MapcheteConfigError):
        mapchete.open(config)


def test_old_style_metadata(old_style_metadata_json, old_geodetic_shape_metadata_json):
    # deprecated CRS definitions
    with pytest.deprecated_call():
        assert read_output_metadata(old_style_metadata_json)
    # deprecated geodetic shape
    with pytest.deprecated_call():
        params = read_output_metadata(old_geodetic_shape_metadata_json)
        assert params["pyramid"].grid.type == "geodetic"


def test_driver_from_extension_tif():
    assert driver_from_extension("tif") == "raster_file"


def test_driver_from_extension_jp2():
    assert driver_from_extension("jp2") == "raster_file"


def test_driver_from_extension_geojson():
    assert driver_from_extension("geojson") == "vector_file"


def test_driver_from_extension_shp():
    assert driver_from_extension("shp") == "vector_file"


def test_driver_from_extension_invalid():
    with pytest.raises(ValueError):
        driver_from_extension("invalid")


def test_load_metadata_pyramid(driver_metadata_dict):
    loaded = load_metadata(driver_metadata_dict)
    assert isinstance(loaded["pyramid"], BufferedTilePyramid)


def test_dump_metadata_pyramid(driver_output_params_dict):
    dumped = dump_metadata(driver_output_params_dict)
    assert isinstance(dumped, dict)


def test_dump_metadata_datetime(driver_output_params_dict):
    dumped = dump_metadata(driver_output_params_dict)
    assert isinstance(dumped["driver"]["time"]["start"], str)
    assert isinstance(dumped["driver"]["time"]["end"], str)


def test_dump_metadata_datetime_list(driver_output_params_dict):
    dumped = dump_metadata(driver_output_params_dict)
    for t in dumped["driver"]["time"]["steps"]:
        assert isinstance(t, str)


def test_load_metadata_datetime(driver_output_params_dict):
    loaded = load_metadata(dump_metadata(driver_output_params_dict))
    assert isinstance(loaded["driver"]["time"]["start"], datetime.date)


def test_load_metadata_datetime_list(driver_output_params_dict):
    loaded = load_metadata(dump_metadata(driver_output_params_dict))
    for t in loaded["driver"]["time"]["steps"]:
        assert isinstance(t, datetime.date)
