#!/usr/bin/env python

# from numpy import stack, ndarray
from numpy.ma import MaskedArray
import os

from .io_funcs import RESAMPLING_METHODS
from .numpy_io import read_numpy

class NumpyTile(object):
    """
    Class representing a tile (existing or virtual) of target pyramid from a
    Mapchete NumPy process output.
    """
    def __init__(
        self,
        input_mapchete,
        tile,
        pixelbuffer=0,
        resampling="nearest"
        ):

        try:
            assert os.path.isfile(input_mapchete.config.process_file)
        except:
            raise IOError("input file does not exist: %s" %
                input_mapchete.config.process_file)

        try:
            assert pixelbuffer == 0
        except:
            raise NotImplementedError(
                "pixelbuffers for NumPy data not yet supported"
            )

        try:
            assert isinstance(pixelbuffer, int)
        except:
            raise ValueError("pixelbuffer must be an integer")

        try:
            assert resampling in RESAMPLING_METHODS
        except:
            raise ValueError("resampling method %s not found." % resampling)

        self.process = input_mapchete
        self.tile_pyramid = self.process.tile_pyramid
        self.tile = tile
        self.input_file = input_mapchete
        self.pixelbuffer = pixelbuffer
        self.resampling = resampling
        self.profile = self._read_metadata()
        self.affine = self.profile["affine"]
        self.nodata = self.profile["nodata"]
        self.indexes = self.profile["count"]
        self.dtype = self.profile["dtype"]
        self.crs = self.tile_pyramid.crs
        self.shape = (self.profile["width"], self.profile["height"])

    def __enter__(self):
        return self

    def __exit__(self, t, v, tb):
        # TODO cleanup
        pass

    def _read_metadata(self):
        """
        Returns a rasterio-like metadata dictionary adapted to tile.
        """
        out_meta = self.process.output.profile
        # create geotransform
        px_size = self.tile_pyramid.pixel_x_size(self.tile.zoom)
        left, bottom, right, top = self.tile.bounds(
            pixelbuffer=self.pixelbuffer
            )
        tile_geotransform = (left, px_size, 0.0, top, 0.0, -px_size)
        out_meta.update(
            width=self.tile.width+2*self.pixelbuffer,
            height=self.tile.height+2*self.pixelbuffer,
            transform=tile_geotransform,
            affine=self.tile.affine(pixelbuffer=self.pixelbuffer)
        )
        return out_meta

    def read(self):
        """
        Generates numpy arrays from input process bands.
        - dst_tile: this tile (self.tile)
        - src_tile(s): original MapcheteProcess pyramid tile
        Note: this is a semi-hacky variation as it uses an os.system call to
        generate a temporal mosaic using the gdalbuildvrt command.
        """

        tile = self.process.tile(self.tile)

        if tile.exists():
            return read_numpy(tile.path)
        else:
            return "empty"
        #
        # else:
        #     empty_array =  ma.masked_array(
        #         ma.zeros(
        #             self.shape,
        #             dtype=self.dtype
        #         ),
        #         mask=True
        #         )
        #     return (
        #         empty_array
        #     )


    def is_empty(self):
        """
        Returns true if all items are masked.
        """
        src_bbox = self.input_file.config.process_area(self.tile.zoom)
        tile_geom = self.tile.bbox(
            pixelbuffer=self.pixelbuffer
        )
        if not tile_geom.intersects(src_bbox):
            return True

        tile = self.process.tile(self.tile)

        if not tile.exists():
            return True
        else:
            return False

        all_bands_empty = True
        for band in self.read():
            if not isinstance(band, MaskedArray):
                all_bands_empty = False
                break
            if not band.mask.all():
                all_bands_empty = False
                break

        return all_bands_empty