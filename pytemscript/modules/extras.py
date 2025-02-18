from typing import Optional, Dict, Tuple, Union
import os
import math
import logging
from pathlib import Path

from ..utils.enums import ImagePixelType, AcqImageFileFormat, StageAxes, MeasurementUnitType


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

    def __init__(self, x: float, y: float):
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

    def __add__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector') -> 'Vector':
        return Vector(self.x - other.x, self.y - other.y)

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

    def __eq__(self, other: Union['Vector', Tuple]) -> bool:
        if isinstance(other, tuple):
            return (self.x, self.y) == other
        elif isinstance(other, Vector):
            return self.x == other.x and self.y == other.y
        return False

    def __neg__(self) -> 'Vector':
        return Vector(-self.x, -self.y)


class BaseImage:
    """ Acquired image basic object. """
    def __init__(self,
                 obj,
                 name: Optional[str] = None,
                 isAdvanced: bool = False,
                 **kwargs):
        self._img = obj
        self._name = name
        self._isAdvanced = isAdvanced
        self._kwargs = kwargs

    def _get_metadata(self, obj):
        raise NotImplementedError

    @property
    def name(self) -> Optional[str]:
        """ Image name. """
        return self._name if self._isAdvanced else self._img.Name

    @property
    def width(self):
        """ Image width in pixels. """
        return None

    @property
    def height(self):
        """ Image height in pixels. """
        return None

    @property
    def bit_depth(self):
        """ Bit depth. """
        return None

    @property
    def pixel_type(self):
        """ Image pixels type: uint, int or float. """
        return None

    @property
    def data(self):
        """ Returns actual image object as numpy array. """
        return None

    @property
    def metadata(self):
        """ Returns a metadata dict for advanced camera image. """
        return self._get_metadata(self._img) if self._isAdvanced else None

    def save(self, filename: Path, normalize: bool = False):
        """ Save acquired image to a file.

        :param filename: File path
        :type filename: str
        :param normalize: Normalize image, only for non-MRC format
        :type normalize: bool
        """
        raise NotImplementedError


class Image(BaseImage):
    """ Acquired image object. """
    def __init__(self,
                 obj,
                 name: Optional[str] = None,
                 isAdvanced: bool = False,
                 **kwargs):
        super().__init__(obj, name, isAdvanced, **kwargs)

    def _get_metadata(self, obj) -> Dict:
        return {item.Key: item.ValueAsString for item in obj.Metadata}

    @property
    def width(self) -> int:
        """ Image width in pixels. """
        return self._img.Width

    @property
    def height(self) -> int:
        """ Image height in pixels. """
        return self._img.Height

    @property
    def bit_depth(self) -> str:
        """ Bit depth. """
        return self._img.BitDepth if self._isAdvanced else self._img.Depth

    @property
    def pixel_type(self) -> str:
        """ Image pixels type: uint, int or float. """
        if self._isAdvanced:
            return ImagePixelType(self._img.PixelType).name
        else:
            return ImagePixelType.SIGNED_INT.name

    @property
    def data(self):
        """ Returns actual image object as numpy int32 array. """
        from comtypes.safearray import safearray_as_ndarray
        with safearray_as_ndarray:
            data = self._img.AsSafeArray
        return data

    def save(self,
             filename: Path,
             normalize: bool = False,
             overwrite: bool = False) -> None:
        """ Save acquired image to a file.

        :param filename: File path
        :type filename: str
        :param normalize: Normalize image, only for non-MRC format
        :type normalize: bool
        :param overwrite: Overwrite existing file
        :type overwrite: bool
        """
        fmt = os.path.splitext(filename)[1].upper().replace(".", "")
        if fmt == "MRC":
            logging.info("Convert to int16 since MRC does not support int32")
            import mrcfile
            with mrcfile.new(filename, overwrite=overwrite) as mrc:
                if self.metadata is not None:
                    mrc.voxel_size = float(self.metadata['PixelSize.Width']) * 1e10
                mrc.set_data(self.data.astype("int16"))
        else:
            # use scripting method to save in other formats
            if self._isAdvanced:
                self._img.SaveToFile(filename)
            else:
                try:
                    fn_format = AcqImageFileFormat[fmt].value
                except KeyError:
                    raise NotImplementedError("Format %s is not supported" % fmt)
                self._img.AsFile(filename, fn_format, normalize)


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
        pos = {key: getattr(self.com_object, key.upper()) * 1e6 for key in 'xyz'}
        if a:
            pos['a'] = math.degrees(self.com_object.A)
            pos['b'] = None
        if b:
            pos['b'] = math.degrees(self.com_object.B)

        return pos

    def limits(self) -> Dict:
        """ Returns a dict with stage move limits. """
        limits = {}
        for axis in 'xyzab':
            data = self.com_object.AxisData(StageAxes[axis.upper()].value)
            limits[axis] = {
                'min': data.MinPos,
                'max': data.MaxPos,
                'unit': MeasurementUnitType(data.UnitType).name
            }

        return limits
