"""Functions for reading and writing data."""

from mapchete.io._json import read_json, write_json
from mapchete.io._misc import (
    copy,
    get_best_zoom_level,
    get_boto3_bucket,
    get_segmentize_value,
    tile_to_zoom_level,
)
from mapchete.io.raster import rasterio_open
from mapchete.io.settings import GDAL_HTTP_OPTS
from mapchete.io.vector import fiona_open
from mapchete.path import (
    MPath,
    absolute_path,
    fs_from_path,
    makedirs,
    path_exists,
    path_is_remote,
    relative_path,
    tiles_exist,
)

__all__ = [
    "copy",
    "fs_from_path",
    "GDAL_HTTP_OPTS",
    "get_best_zoom_level",
    "get_segmentize_value",
    "tile_to_zoom_level",
    "path_is_remote",
    "path_exists",
    "tiles_exist",
    "absolute_path",
    "relative_path",
    "makedirs",
    "Path",
    "write_json",
    "read_json",
    "get_boto3_bucket",
    "MPath",
    "fiona_open",
    "rasterio_open",
]
