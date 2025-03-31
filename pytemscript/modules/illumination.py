from typing import Union, List, Tuple
import math

from .extras import Vector
from ..utils.misc import RequestBody
from ..utils.enums import CondenserLensSystem, CondenserMode, DarkFieldMode, IlluminationMode


class Illumination:
    """ Illumination functions. """
    __slots__ = ("__client", "__condenser_type", "__id")

    def __init__(self, client, condenser_type):
        self.__client = client
        self.__condenser_type = condenser_type
        self.__id = "tem.Illumination"
    
    @property
    def __has_3cond(self) -> bool:
        return self.__condenser_type == CondenserLensSystem.THREE_CONDENSER_LENSES.name

    @property
    def spotsize(self) -> int:
        """ Spotsize number, usually 1 to 11. (read/write) """
        body = RequestBody(attr=self.__id + ".SpotsizeIndex", validator=int)

        return self.__client.call(method="get", body=body)

    @spotsize.setter
    def spotsize(self, value: int) -> None:
        if not (0 < int(value) < 12):
            raise ValueError("%s is outside of range 1-11" % value)

        body = RequestBody(attr=self.__id + ".SpotsizeIndex", value=value)
        self.__client.call(method="set", body=body)

    @property
    def intensity(self) -> float:
        """ Intensity / C2 condenser lens value. (read/write) """
        body = RequestBody(attr=self.__id + ".Intensity", validator=float)

        return self.__client.call(method="get", body=body)

    @intensity.setter
    def intensity(self, value: float) -> None:
        if not (0.0 <= value <= 1.0):
            raise ValueError("%s is outside of range 0.0-1.0" % value)

        body = RequestBody(attr=self.__id + ".Intensity", value=value)
        self.__client.call(method="set", body=body)

    @property
    def intensity_zoom(self) -> bool:
        """ Intensity zoom (AutoZoom on Krios). Set to False to disable. (read/write) """
        body = RequestBody(attr=self.__id + ".IntensityZoomEnabled", validator=bool)

        return self.__client.call(method="get", body=body)

    @intensity_zoom.setter
    def intensity_zoom(self, value: bool) -> None:
        body = RequestBody(attr=self.__id + ".IntensityZoomEnabled", value=bool(value))
        self.__client.call(method="set", body=body)

    @property
    def intensity_limit(self) -> bool:
        """ Intensity limit. Set to False to disable. (read/write) """
        if self.__has_3cond:
            raise NotImplementedError("Intensity limit exists only on 2-condenser lens systems.")
        else:
            body = RequestBody(attr=self.__id + ".IntensityLimitEnabled", validator=bool)
            return self.__client.call(method="get", body=body)

    @intensity_limit.setter
    def intensity_limit(self, value: bool) -> None:
        if self.__has_3cond:
            raise NotImplementedError("Intensity limit exists only on 2-condenser lens systems.")
        else:
            body = RequestBody(attr=self.__id + ".IntensityLimitEnabled", value=bool(value))
            self.__client.call(method="set", body=body)

    @property
    def beam_shift(self) -> Vector:
        """ Beam shift X and Y in um. (read/write) """
        shx = RequestBody(attr=self.__id + ".Shift.X", validator=float)
        shy = RequestBody(attr=self.__id + ".Shift.Y", validator=float)

        x = self.__client.call(method="get", body=shx)
        y = self.__client.call(method="get", body=shy)

        return Vector(x, y) * 1e6

    @beam_shift.setter
    def beam_shift(self, vector: Union[Vector, List[float], Tuple[float, float]]) -> None:
        value = Vector.convert_to(vector) * 1e-6
        body = RequestBody(attr=self.__id + ".Shift", value=value)
        self.__client.call(method="set", body=body)

    @property
    def rotation_center(self) -> Vector:
        """ Rotation center X and Y in mrad. (read/write)

        Depending on the scripting version, the values might need
        scaling by 6.0 to get mrads.
        """
        rotx = RequestBody(attr=self.__id + ".RotationCenter.X", validator=float)
        roty = RequestBody(attr=self.__id + ".RotationCenter.Y", validator=float)

        x = self.__client.call(method="get", body=rotx)
        y = self.__client.call(method="get", body=roty)

        return Vector(x, y) * 1e3

    @rotation_center.setter
    def rotation_center(self, vector: Union[Vector, List[float], Tuple[float, float]]) -> None:
        value = Vector.convert_to(vector) * 1e-3
        body = RequestBody(attr=self.__id + ".RotationCenter", value=value)
        self.__client.call(method="set", body=body)

    @property
    def condenser_stigmator(self) -> Vector:
        """ C2 condenser stigmator X and Y. (read/write) """
        stigx = RequestBody(attr=self.__id + ".CondenserStigmator.X", validator=float)
        stigy = RequestBody(attr=self.__id + ".CondenserStigmator.Y", validator=float)

        return Vector(self.__client.call(method="get", body=stigx),
                      self.__client.call(method="get", body=stigy))

    @condenser_stigmator.setter
    def condenser_stigmator(self, vector: Union[Vector, List[float], Tuple[float, float]]) -> None:
        value = Vector.convert_to(vector)
        value.set_limits(-1.0, 1.0)
        body = RequestBody(attr=self.__id + ".CondenserStigmator", value=value)
        self.__client.call(method="set", body=body)

    @property
    def illuminated_area(self) -> float:
        """ Illuminated area in um. Works only on 3-condenser lens systems. (read/write) """
        if not self.__has_3cond:
            raise NotImplementedError("Illuminated area exists only on 3-condenser lens systems.")
        if self.condenser_mode == CondenserMode.PARALLEL.name:
            body = RequestBody(attr=self.__id + ".IlluminatedArea", validator=float)
            return self.__client.call(method="get", body=body) * 1e6
        else:
            raise RuntimeError("Condenser is not in Parallel mode.")

    @illuminated_area.setter
    def illuminated_area(self, value: float) -> None:
        if not self.__has_3cond:
            raise NotImplementedError("Illuminated area exists only on 3-condenser lens systems.")
        if self.condenser_mode == CondenserMode.PARALLEL.name:
            body = RequestBody(attr=self.__id + ".IlluminatedArea", value=value*1e-6)
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError("Condenser is not in Parallel mode.")

    @property
    def probe_defocus(self) -> float:
        """ Probe defocus. Works only on 3-condenser lens systems in probe mode. """
        if not self.__has_3cond:
            raise NotImplementedError("Probe defocus exists only on 3-condenser lens systems.")
        if self.condenser_mode == CondenserMode.PROBE.name:
            body = RequestBody(attr=self.__id + ".ProbeDefocus", validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise RuntimeError("Condenser is not in Probe mode.")

    @property
    def convergence_angle(self) -> float:
        """ Convergence angle. Works only on 3-condenser lens systems in probe mode. """
        if not self.__has_3cond:
            raise NotImplementedError("Probe defocus exists only on 3-condenser lens systems.")
        if self.condenser_mode == CondenserMode.PROBE.name:
            body = RequestBody(attr=self.__id + ".ConvergenceAngle", validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise RuntimeError("Condenser is not in Probe mode.")

    @property
    def C3ImageDistanceParallelOffset(self) -> float:
        """ C3 image distance parallel offset. Works only on 3-condenser lens systems. (read/write)

        This value takes the place previously of the Intensity value. The Intensity value
        changed the focusing of the diffraction pattern at the back-focal plane (MF-Y in Beam Settings
        control panel) but was rather independent of the illumination optics. As
        such it changed the size of the illumination but the illuminated area
        parameter was not influenced. To get rid of this problematic bypass,
        the C3 image distance offset has been created which effectively does
        the same focusing but now from within the illumination optics so the
        illuminated area remains correct. The range is quite small,  +/-0.02
        """
        if not self.__has_3cond:
            raise NotImplementedError("C3ImageDistanceParallelOffset exists only on 3-condenser lens systems.")
        if self.condenser_mode == CondenserMode.PARALLEL.name:
            body = RequestBody(attr=self.__id + ".C3ImageDistanceParallelOffset", validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise RuntimeError("Condenser is not in Probe mode.")

    @C3ImageDistanceParallelOffset.setter
    def C3ImageDistanceParallelOffset(self, value: float) -> None:
        if not self.__has_3cond:
            raise NotImplementedError("C3ImageDistanceParallelOffset exists only on 3-condenser lens systems.")
        if self.condenser_mode == CondenserMode.PARALLEL.name:
            body = RequestBody(attr=self.__id + ".C3ImageDistanceParallelOffset", value=value)
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError("Condenser is not in PARALLEL mode.")

    @property
    def mode(self) -> str:
        """ Illumination mode: microprobe or nanoprobe. IlluminationMode enum (read/write)

        (Nearly) no effect for low magnifications (LM).
        """
        body = RequestBody(attr=self.__id + ".Mode", validator=int)
        result = self.__client.call(method="get", body=body)

        return IlluminationMode(result).name

    @mode.setter
    def mode(self, value: IlluminationMode) -> None:
        body = RequestBody(attr=self.__id + ".Mode", value=value)
        self.__client.call(method="set", body=body)

    @property
    def dark_field(self) -> str:
        """ Dark field mode: cartesian, conical or off. DarkFieldMode enum (read/write) """
        body = RequestBody(attr=self.__id + ".DFMode", validator=int)
        result = self.__client.call(method="get", body=body)

        return DarkFieldMode(result).name

    @dark_field.setter
    def dark_field(self, value: DarkFieldMode) -> None:
        body = RequestBody(attr=self.__id + ".DFMode", value=value)
        self.__client.call(method="set", body=body)

    @property
    def condenser_mode(self) -> str:
        """ Mode of the illumination system: parallel or probe. CondenserMode enum (read/write) """
        if self.__has_3cond:
            body = RequestBody(attr=self.__id + ".CondenserMode", validator=int)
            result = self.__client.call(method="get", body=body)
            return CondenserMode(result).name
        else:
            raise NotImplementedError("Condenser mode exists only on 3-condenser lens systems.")

    @condenser_mode.setter
    def condenser_mode(self, value: CondenserMode) -> None:
        if self.__has_3cond:
            body = RequestBody(attr=self.__id + ".CondenserMode", value=value)
            self.__client.call(method="set", body=body)
        else:
            raise NotImplementedError("Condenser mode can be changed only on 3-condenser lens systems.")

    @property
    def beam_tilt(self) -> Union[Vector, float]:
        """ Dark field beam tilt relative to the origin stored at
        alignment time. Only operational if dark field mode is active.
        Units: mrad, either in Cartesian (x,y) or polar (conical)
        tilt angles. The accuracy of the beam tilt physical units
        depends on a calibration of the tilt angles. (read/write)
        """
        dfmode = RequestBody(attr=self.__id + ".DFMode", validator=int)
        dftiltx = RequestBody(attr=self.__id + ".Tilt.X", validator=float)
        dftilty = RequestBody(attr=self.__id + ".Tilt.Y", validator=float)

        mode = self.__client.call(method="get", body=dfmode)
        tiltx = self.__client.call(method="get", body=dftiltx) # rad
        tilty = self.__client.call(method="get", body=dftilty) # rad

        if mode == DarkFieldMode.CONICAL:
            tilt = tiltx
            rot = tilty
            return Vector(tilt * math.cos(rot), tilt * math.sin(rot)) * 1e3
        elif mode == DarkFieldMode.CARTESIAN:
            return Vector(tiltx, tilty) * 1e3
        else:  # DF is off
            return Vector(0.0, 0.0)  # Microscope might return nonsense if DFMode is OFF

    @beam_tilt.setter
    def beam_tilt(self, tilt: Union[Vector, float, List[float], Tuple[float, float]]) -> None:
        body = RequestBody(attr=self.__id + ".DFMode", validator=int)
        mode = self.__client.call(method="get", body=body)

        if isinstance(tilt, float):
            tilt = Vector(tilt, tilt)

        tilt = Vector.convert_to(tilt) * 1e-3 # mrad to rad

        if tilt == (0.0, 0.0):
            body = RequestBody(attr=self.__id + ".Tilt", value=tilt)
            self.__client.call(method="set", body=body)

            body = RequestBody(attr=self.__id + ".DFMode", value=DarkFieldMode.OFF)
            self.__client.call(method="set", body=body)

        elif mode == DarkFieldMode.CONICAL:
            value = Vector(math.sqrt(tilt.x ** 2 + tilt.y ** 2),
                           math.atan2(tilt.y, tilt.x))
            body = RequestBody(attr=self.__id + ".Tilt", value=value)
            self.__client.call(method="set", body=body)

        elif mode == DarkFieldMode.CARTESIAN:
            body = RequestBody(attr=self.__id + ".Tilt", value=tilt)
            self.__client.call(method="set", body=body)

        else:
            raise ValueError("Dark field mode is OFF. You cannot set beam tilt.")
