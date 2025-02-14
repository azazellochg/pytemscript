from .extras import Vector
from ..utils.enums import InstrumentMode


class Stem:
    """ STEM functions. """
    __slots__ = ("__client", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__err_msg = "Microscope not in STEM mode"

    @property
    def is_available(self) -> bool:
        """ Returns whether the microscope has a STEM system or not. """
        return self.__client.has("tem.InstrumentModeControl.StemAvailable")

    def enable(self) -> None:
        """ Switch to STEM mode."""
        if self.is_available:
            self.__client.set("tem.InstrumentModeControl.InstrumentMode", InstrumentMode.STEM)
        else:
            raise RuntimeError(self.__err_msg)

    def disable(self) -> None:
        """ Switch back to TEM mode. """
        self.__client.set("tem.InstrumentModeControl.InstrumentMode", InstrumentMode.TEM)

    @property
    def magnification(self) -> float:
        """ The magnification value in STEM mode. (read/write)"""
        if self.__client.get("tem.InstrumentModeControl.InstrumentMode") == InstrumentMode.STEM:
            return self.__client.get("tem.Illumination.StemMagnification")
        else:
            raise RuntimeError(self.__err_msg)

    @magnification.setter
    def magnification(self, mag: int) -> None:
        if self.__client.get("tem.InstrumentModeControl.InstrumentMode") == InstrumentMode.STEM:
            self.__client.set("tem.Illumination.StemMagnification", float(mag))
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def rotation(self) -> float:
        """ The STEM rotation angle (in mrad). (read/write)"""
        if self.__client.get("tem.InstrumentModeControl.InstrumentMode") == InstrumentMode.STEM:
            return self.__client.get("tem.Illumination.StemRotation") * 1e3
        else:
            raise RuntimeError(self.__err_msg)

    @rotation.setter
    def rotation(self, rot: float) -> None:
        if self.__client.get("tem.InstrumentModeControl.InstrumentMode") == InstrumentMode.STEM:
            self.__client.set("tem.Illumination.StemRotation", float(rot) * 1e-3)
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def scan_field_of_view(self) -> tuple:
        """ STEM full scan field of view. (read/write)"""
        if self.__client.get("tem.InstrumentModeControl.InstrumentMode") == InstrumentMode.STEM:
            return (self.__client.get("tem.Illumination.StemFullScanFieldOfView.X"),
                    self.__client.get("tem.Illumination.StemFullScanFieldOfView.Y"))
        else:
            raise RuntimeError(self.__err_msg)

    @scan_field_of_view.setter
    def scan_field_of_view(self, values: tuple) -> None:
        if self.__client.get("tem.InstrumentModeControl.InstrumentMode") == InstrumentMode.STEM:
            new_value = Vector(*values)
            self.__client.set("tem.Illumination.StemFullScanFieldOfView", new_value)
        else:
            raise RuntimeError(self.__err_msg)
