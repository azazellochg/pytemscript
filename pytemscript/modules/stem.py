from typing import Tuple

from .extras import Vector
from ..utils.misc import RequestBody
from ..utils.enums import InstrumentMode


class Stem:
    """ STEM functions. """
    __slots__ = ("__client", "__id", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem.InstrumentModeControl"
        self.__err_msg = "Microscope not in STEM mode"

    @property
    def is_available(self) -> bool:
        """ Returns whether the microscope _has a STEM system or not. """
        body = RequestBody(attr=self.__id + ".StemAvailable", validator=bool)

        return self.__client.call(method="has", body=body)

    def enable(self) -> None:
        """ Switch to STEM mode."""
        if self.is_available:
            body = RequestBody(attr=self.__id + ".InstrumentMode", value=InstrumentMode.STEM)
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    def disable(self) -> None:
        """ Switch back to TEM mode. """
        body = RequestBody(attr=self.__id + ".InstrumentMode", value=InstrumentMode.TEM)
        self.__client.call(method="set", body=body)

    @property
    def magnification(self) -> int:
        """ The magnification value in STEM mode. (read/write)"""
        body = RequestBody(attr=self.__id + ".InstrumentMode", validator=int)

        if self.__client.call(method="get", body=body) == InstrumentMode.STEM:
            body = RequestBody(attr=self.__id + ".StemMagnification", validator=float)
            return int(self.__client.call(method="get", body=body))
        else:
            raise RuntimeError(self.__err_msg)

    @magnification.setter
    def magnification(self, mag: int) -> None:
        body = RequestBody(attr=self.__id + ".InstrumentMode", validator=int)

        if self.__client.call(method="get", body=body) == InstrumentMode.STEM:
            body = RequestBody(attr="tem.Illumination.StemMagnification", value=float(mag))
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def rotation(self) -> float:
        """ The STEM rotation angle (in mrad). (read/write)"""
        body = RequestBody(attr=self.__id + ".InstrumentMode", validator=int)

        if self.__client.call(method="get", body=body) == InstrumentMode.STEM:
            body = RequestBody(attr="tem.Illumination.StemRotation", validator=float)
            return self.__client.call(method="get", body=body) * 1e3
        else:
            raise RuntimeError(self.__err_msg)

    @rotation.setter
    def rotation(self, rot: float) -> None:
        body = RequestBody(attr=self.__id + ".InstrumentMode", validator=int)

        if self.__client.call(method="get", body=body) == InstrumentMode.STEM:
            body = RequestBody(attr="tem.Illumination.StemRotation",
                                  value=float(rot) * 1e-3)
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def scan_field_of_view(self) -> Tuple:
        """ STEM full scan field of view. (read/write)"""
        body = RequestBody(attr=self.__id + ".InstrumentMode", validator=int)

        if self.__client.call(method="get", body=body) == InstrumentMode.STEM:
            fov_x = RequestBody(attr="tem.Illumination.StemFullScanFieldOfView.X", validator=float)
            fov_y = RequestBody(attr="tem.Illumination.StemFullScanFieldOfView.Y", validator=float)

            x = self.__client.call(method="get", body=fov_x)
            y = self.__client.call(method="get", body=fov_y)

            return (x, y)
        else:
            raise RuntimeError(self.__err_msg)

    @scan_field_of_view.setter
    def scan_field_of_view(self, values: Tuple) -> None:
        body = RequestBody(attr=self.__id + ".InstrumentMode", validator=int)

        if self.__client.call(method="get", body=body) == InstrumentMode.STEM:
            new_value = Vector(*values)
            body = RequestBody(attr="tem.Illumination.StemFullScanFieldOfView", value=new_value)
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError(self.__err_msg)
