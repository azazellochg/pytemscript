from typing import Optional, Dict, Tuple, Union
from datetime import datetime
import math
import logging
from pathlib import Path
import numpy as np
from collections import OrderedDict

try:
    import PIL.Image as PilImage
    import PIL.TiffImagePlugin as PilTiff
except ImportError:
    print("Pillow library not found, you won't be able to "
          "save images in non-MRC format.")


from ..utils.enums import StageAxes, MeasurementUnitType


class Vector:
    """ Utility object with two float attributes.

    :param x: X value
    :type x: float
    :param y: Y value
    :type y: float

    Usage:
            >>> from pytemscript.modules import Vector
            >>> vector = Vector(0.03, 0.02)
            >>> microscope.optics.illumination.beam_shift = vector
            >>> vector *= 2
            >>> print(vector)
            (0.06, 0.04)
            >>> vector.set(-0.5, -0.06)
            >>> print(vector)
            (-0.5, -0.06)
    """
    __slots__ = ("x", "y", "__min", "__max")

    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y
        self.__min = None
        self.__max = None

    def __repr__(self):
        return "Vector(x=%f, y=%f)" % (self.x, self.y)

    def __str__(self):
        return "(%f, %f)" % (self.x, self.y)

    def set_limits(self, min_value: float, max_value: float) -> None:
        """Set the range limits for the vector for both X and Y."""
        self.__min = min_value
        self.__max = max_value

    @property
    def has_limits(self) -> bool:
        """Check if range limits are defined."""
        return self.__min is not None and self.__max is not None

    def check_limits(self) -> None:
        """Validate that the vector's values are within the set limits."""
        if self.has_limits:
            if any(v < self.__min or v > self.__max for v in self.get()):
                msg = "One or more values (%s) are outside of range (%f, %f)" % (self.get(), self.x, self.y)
                logging.error(msg)
                raise ValueError(msg)

    def get(self) -> Tuple:
        """Return the vector components as a tuple."""
        return self.x, self.y

    def set(self, value: Tuple[float, float]) -> None:
        """ Update values from a tuple. """
        if not isinstance(value, tuple):
            raise TypeError("Expected a tuple of floats")
        else:
            self.x, self.y = value

    def __add__(self, other: Union['Vector', Tuple]) -> 'Vector':
        if isinstance(other, tuple):
            return Vector(self.x + other[0], self.y + other[1])
        elif isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        else:
            raise TypeError("Expected a Vector or a tuple")

    def __sub__(self, other: Union['Vector', Tuple]) -> 'Vector':
        if isinstance(other, tuple):
            return Vector(self.x - other[0], self.y - other[1])
        elif isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        else:
            raise TypeError("Expected a Vector or a tuple")

    def __mul__(self, scalar: float) -> 'Vector':
        return Vector(self.x * scalar, self.y * scalar)

    def __imul__(self, scalar: float) -> 'Vector':
        if not isinstance(scalar, (int, float)):
            raise ValueError("Scalar must be a number")
        self.x *= scalar
        self.y *= scalar
        return self

    def __truediv__(self, scalar: float) -> 'Vector':
        if scalar == 0:
            raise ValueError("Cannot divide by zero")
        return Vector(self.x / scalar, self.y / scalar)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, tuple):
            return (self.x, self.y) == other
        elif isinstance(other, Vector):
            return self.x == other.x and self.y == other.y
        return False

    def __neg__(self) -> 'Vector':
        return Vector(-self.x, -self.y)


class Image:
    """ Acquired image basic object. """
    def __init__(self,
                 data: np.ndarray,  # int16
                 name: str,
                 metadata: Dict) -> None:
        self.data = data
        self.name = name
        self.metadata = metadata
        self.timestamp = datetime.now()

    def __create_tiff_tags(self):
        """Create TIFF tags from metadata. """
        tiff_tags = PilTiff.ImageFileDirectory_v2()

        # Basic Image Metadata
        metadata = self.metadata
        tiff_tags[PilTiff.IMAGEWIDTH] = metadata["width"]
        tiff_tags[PilTiff.IMAGELENGTH] = metadata["height"]
        tiff_tags[PilTiff.COMPRESSION] = 1  # raw
        tiff_tags[PilTiff.RESOLUTION_UNIT] = 3  # cm
        tiff_tags[PilTiff.IMAGEDESCRIPTION] = self.name
        tiff_tags[PilTiff.DATE_TIME] = self.timestamp.strftime("%Y:%m:%d %H:%M:%S")

        # Detector Name
        detector_name = metadata.get("DetectorName")
        if detector_name:
            tiff_tags[271] = detector_name  # Tag 271 (MAKE)

        # Pixel Size (Resolution)
        pixel_width = metadata.get("PixelSize.Width")  # angstroms
        pixel_height = metadata.get("PixelSize.Height")
        if pixel_width and pixel_height:
            scale = 1e8  # convert to cm
            tiff_tags[PilTiff.X_RESOLUTION] = (pixel_width * scale, 1)
            tiff_tags[PilTiff.Y_RESOLUTION] = (pixel_height * scale, 1)

        # Bit Depth & Color Interpretation
        bit_depth = metadata.get("bit_depth", 16)
        tiff_tags[PilTiff.BITSPERSAMPLE] = (bit_depth,)
        tiff_tags[PilTiff.PHOTOMETRIC_INTERPRETATION] = 1  # BlackIsZero

        return tiff_tags

    def save(self,
             fn: Union[Path, str],
             overwrite: bool = False) -> None:
        """ Save acquired image to a file as int16.

        :param fn: File path
        :param overwrite: Overwrite existing file
        """
        if isinstance(fn, str):
            fn = Path(fn)

        ext = fn.suffix.lower()

        if ext == ".mrc":
            import mrcfile
            with mrcfile.new(fn, overwrite=overwrite) as mrc:
                if 'PixelSize.Width' in self.metadata:
                    mrc.voxel_size = float(self.metadata['PixelSize.Width']) * 1e10
                mrc.set_data(self.data)

        elif ext in [".tiff", ".tif", ".png"]:
            if fn.exists() and not overwrite:
                raise FileExistsError("File %s already exists, use overwrite flag" % fn.resolve())

            logging.getLogger("PIL").setLevel(logging.INFO)
            pil_image = PilImage.fromarray(self.data, mode='I;16')
            tiff_tags = self.__create_tiff_tags() if ext != ".png" else None
            pil_image.save(fn, format=None, tiffinfo=tiff_tags)

        else:
            raise NotImplementedError("Unsupported file format: %s" % ext)

        logging.info("File saved: %s", fn.resolve())


class SpecialObj:
    """ Wrapper class for complex methods to be executed on a COM object. """
    def __init__(self, com_object):
        self.com_object = com_object


class StageObj(SpecialObj):
    """ Wrapper around stage / piezo stage COM object. """

    def set(self,
            axes: int = 0,
            speed: Optional[float] = None,
            method: str = "MoveTo",
            **kwargs) -> None:
        """ Execute stage move to a new position. """
        if method not in ["MoveTo", "GoTo", "GoToWithSpeed"]:
            raise NotImplementedError("Method %s is not implemented" % method)

        pos = self.com_object.Position
        for key, value in kwargs.items():
            setattr(pos, key.upper(), float(value))

        if speed is not None:
            getattr(self.com_object, method)(pos, axes, speed)
        else:
            getattr(self.com_object, method)(pos, axes)

    def get(self, a=False, b=False) -> Dict:
        """ The current position of the stage/piezo stage (x,y,z in um).
        Set a and b to True if you want to retrieve them as well.
        x,y,z are in um and a,b in deg

        If retrieving velocity, return the speed of the piezo stage instead.
        x,y,z are in um/s and a,b in deg/s
        """
        pos = OrderedDict((key, getattr(self.com_object, key.upper()) * 1e6) for key in 'xyz')
        if a:
            pos['a'] = math.degrees(self.com_object.A)
            pos['b'] = None
        if b:
            pos['b'] = math.degrees(self.com_object.B)

        return pos

    def limits(self) -> Dict:
        """ Returns a dict with stage move limits. """
        limits = OrderedDict()
        for axis in 'xyzab':
            data = self.com_object.AxisData(StageAxes[axis.upper()].value)
            limits[axis] = {
                'min': data.MinPos,
                'max': data.MaxPos,
                'unit': MeasurementUnitType(data.UnitType).name
            }

        return limits
