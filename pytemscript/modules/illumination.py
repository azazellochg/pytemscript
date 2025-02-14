from typing import Union
import math

from .extras import Vector
from ..utils.enums import CondenserLensSystem, CondenserMode, DarkFieldMode, IlluminationMode


class Illumination:
    """ Illumination functions. """
    __slots__ = ("__client", "__condenser_type", "__shortcut")

    def __init__(self, client, condenser_type):
        self.__client = client
        self.__condenser_type = condenser_type
        self.__shortcut = "tem.Illumination"
    
    @property
    def __has_3cond(self) -> bool:
        return self.__condenser_type == CondenserLensSystem.THREE_CONDENSER_LENSES.name

    @property
    def spotsize(self) -> int:
        """ Spotsize number, usually 1 to 11. (read/write)"""
        return int(self.__client.get(self.__shortcut + ".SpotsizeIndex"))

    @spotsize.setter
    def spotsize(self, value: int) -> None:
        if not (1 <= int(value) <= 11):
            raise ValueError("%s is outside of range 1-11" % value)
        self.__client.set(self.__shortcut + ".SpotsizeIndex", int(value))

    @property
    def intensity(self) -> float:
        """ Intensity / C2 condenser lens value. (read/write)"""
        return self.__client.get(self.__shortcut + ".Intensity")

    @intensity.setter
    def intensity(self, value: float) -> None:
        if not (0.0 <= value <= 1.0):
            raise ValueError("%s is outside of range 0.0-1.0" % value)
        self.__client.set(self.__shortcut + ".Intensity", float(value))

    @property
    def intensity_zoom(self) -> bool:
        """ Intensity zoom. Set to False to disable. (read/write)"""
        return bool(self.__client.get(self.__shortcut + ".IntensityZoomEnabled"))

    @intensity_zoom.setter
    def intensity_zoom(self, value: bool) -> None:
        self.__client.set(self.__shortcut + ".IntensityZoomEnabled", bool(value))

    @property
    def intensity_limit(self) -> bool:
        """ Intensity limit. Set to False to disable. (read/write)"""
        return bool(self.__client.get(self.__shortcut + ".IntensityLimitEnabled"))

    @intensity_limit.setter
    def intensity_limit(self, value: bool) -> None:
        self.__client.set(self.__shortcut + ".IntensityLimitEnabled", bool(value))

    @property
    def beam_shift(self) -> tuple:
        """ Beam shift X and Y in um. (read/write)"""
        return (self.__client.get(self.__shortcut + ".Shift.X") * 1e6,
                self.__client.get(self.__shortcut + ".Shift.Y") * 1e6)

    @beam_shift.setter
    def beam_shift(self, values: tuple) -> None:
        new_value = Vector(values[0] * 1e-6, values[1] * 1e-6)
        self.__client.set(self.__shortcut + ".Shift", new_value)

    @property
    def rotation_center(self) -> tuple:
        """ Rotation center X and Y in mrad. (read/write)
            Depending on the scripting version,
            the values might need scaling by 6.0 to get mrads.
        """
        return (self.__client.get(self.__shortcut + ".RotationCenter.X") * 1e3,
                self.__client.get(self.__shortcut + ".RotationCenter.Y") * 1e3)

    @rotation_center.setter
    def rotation_center(self, values: tuple) -> None:
        new_value = Vector(values[0] * 1e-3, values[1] * 1e-3)
        self.__client.set(self.__shortcut + ".RotationCenter", new_value)

    @property
    def condenser_stigmator(self) -> tuple:
        """ C2 condenser stigmator X and Y. (read/write)"""
        return (self.__client.get(self.__shortcut + ".CondenserStigmator.X"),
                self.__client.get(self.__shortcut + ".CondenserStigmator.Y"))

    @condenser_stigmator.setter
    def condenser_stigmator(self, values: tuple) -> None:
        new_value = Vector(*values)
        new_value.set_limits(-1.0, 1.0)
        self.__client.set(self.__shortcut + ".CondenserStigmator", new_value)

    @property
    def illuminated_area(self) -> float:
        """ Illuminated area. Works only on 3-condenser lens systems. (read/write)"""
        if self.__has_3cond:
            return self.__client.get(self.__shortcut + ".IlluminatedArea")
        else:
            raise NotImplementedError("Illuminated area exists only on 3-condenser lens systems.")

    @illuminated_area.setter
    def illuminated_area(self, value: float) -> None:
        if self.__has_3cond:
            self.__client.set(self.__shortcut + ".IlluminatedArea", float(value))
        else:
            raise NotImplementedError("Illuminated area exists only on 3-condenser lens systems.")

    @property
    def probe_defocus(self) -> float:
        """ Probe defocus. Works only on 3-condenser lens systems. (read/write)"""
        if self.__has_3cond:
            return self.__client.get(self.__shortcut + ".ProbeDefocus")
        else:
            raise NotImplementedError("Probe defocus exists only on 3-condenser lens systems.")

    @probe_defocus.setter
    def probe_defocus(self, value: float) -> None:
        if self.__has_3cond:
            self.__client.set(self.__shortcut + ".ProbeDefocus", float(value))
        else:
            raise NotImplementedError("Probe defocus exists only on 3-condenser lens systems.")

    #TODO: check if the illum. mode is probe?
    @property
    def convergence_angle(self) -> float:
        """ Convergence angle. Works only on 3-condenser lens systems. (read/write)"""
        if self.__has_3cond:
            return self.__client.get(self.__shortcut + ".ConvergenceAngle")
        else:
            raise NotImplementedError("Convergence angle exists only on 3-condenser lens systems.")

    @convergence_angle.setter
    def convergence_angle(self, value: float) -> None:
        if self.__has_3cond:
            self.__client.set(self.__shortcut + ".ConvergenceAngle", float(value))
        else:
            raise NotImplementedError("Convergence angle exists only on 3-condenser lens systems.")

    @property
    def C3ImageDistanceParallelOffset(self) -> float:
        """ C3 image distance parallel offset. Works only on 3-condenser lens systems. (read/write)"""
        if self.__has_3cond:
            return self.__client.get(self.__shortcut + ".C3ImageDistanceParallelOffset")
        else:
            raise NotImplementedError("C3ImageDistanceParallelOffset exists only on 3-condenser lens systems.")

    @C3ImageDistanceParallelOffset.setter
    def C3ImageDistanceParallelOffset(self, value: float) -> None:
        if self.__has_3cond:
            self.__client.set(self.__shortcut + ".C3ImageDistanceParallelOffset", float(value))
        else:
            raise NotImplementedError("C3ImageDistanceParallelOffset exists only on 3-condenser lens systems.")

    @property
    def mode(self) -> str:
        """ Illumination mode: microprobe or nanoprobe. (read/write)"""
        return IlluminationMode(self.__client.get(self.__shortcut + ".Mode")).name

    @mode.setter
    def mode(self, value: IlluminationMode) -> None:
        self.__client.set(self.__shortcut + ".Mode", value)

    @property
    def dark_field(self) -> str:
        """ Dark field mode: cartesian, conical or off. (read/write)"""
        return DarkFieldMode(self.__client.get(self.__shortcut + ".DFMode")).name

    @dark_field.setter
    def dark_field(self, value: DarkFieldMode) -> None:
        self.__client.set(self.__shortcut + ".DFMode", value)

    @property
    def condenser_mode(self) -> str:
        """ Mode of the illumination system: parallel or probe. (read/write)"""
        if self.__has_3cond:
            return CondenserMode(self.__client.get(self.__shortcut + ".CondenserMode")).name
        else:
            raise NotImplementedError("Condenser mode exists only on 3-condenser lens systems.")

    @condenser_mode.setter
    def condenser_mode(self, value: CondenserMode) -> None:
        if self.__has_3cond:
            self.__client.set(self.__shortcut + ".CondenserMode", value)
        else:
            raise NotImplementedError("Condenser mode can be changed only on 3-condenser lens systems.")

    @property
    def beam_tilt(self) -> Union[tuple, float]:
        """ Dark field beam tilt relative to the origin stored at
        alignment time. Only operational if dark field mode is active.
        Units: mrad, either in Cartesian (x,y) or polar (conical)
        tilt angles. The accuracy of the beam tilt physical units
        depends on a calibration of the tilt angles. (read/write)
        """
        mode = self.__client.get(self.__shortcut + ".DFMode")
        tilt = self.__client.get(self.__shortcut + ".Tilt")
        if mode == DarkFieldMode.CONICAL:
            return tilt[0] * 1e3 * math.cos(tilt[1]), tilt[0] * 1e3 * math.sin(tilt[1])
        elif mode == DarkFieldMode.CARTESIAN:
            return tilt * 1e3
        else:
            return 0.0, 0.0  # Microscope might return nonsense if DFMode is OFF

    @beam_tilt.setter
    def beam_tilt(self, tilt: Union[tuple, float]) -> None:
        mode = self.__client.get(self.__shortcut + ".DFMode")

        if isinstance(tilt, float):
            newtilt = [tilt, tilt]
        else:
            newtilt = list(tilt)

        newtilt[0] *= 1e-3
        newtilt[1] *= 1e-3
        if newtilt[0] == 0.0 and newtilt[1] == 0.0:
            self.__client.set(self.__shortcut + ".Tilt", (0.0, 0.0))
            self.__client.set(self.__shortcut + ".DFMode", DarkFieldMode.OFF)
        elif mode == DarkFieldMode.CONICAL:
            self.__client.set(self.__shortcut + ".Tilt",
                              (math.sqrt(newtilt[0] ** 2 + newtilt[1] ** 2), math.atan2(newtilt[1], newtilt[0])))
        elif mode == DarkFieldMode.OFF:
            self.__client.set(self.__shortcut + ".DFMode", DarkFieldMode.CARTESIAN)
            self.__client.set(self.__shortcut + ".Tilt", newtilt[0])
        else:
            self.__client.set(self.__shortcut + ".Tilt", newtilt[0])
