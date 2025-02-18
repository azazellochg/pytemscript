from typing import Dict, Tuple
import logging

from ..utils.misc import RequestBody
from ..utils.enums import (ProjectionMode, ProjectionSubMode, ProjDetectorShiftMode,
                           ProjectionDetectorShift, LensProg)
from .extras import Vector


class Projection:
    """ Projection system functions. """
    __slots__ = ("__client", "__id", "__err_msg", "__magnifications")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem.Projection"
        self.__err_msg = "Microscope is not in diffraction mode"
        self.__magnifications = {}
        self.__find_magnifications()

    def __find_magnifications(self) -> None:
        if not self.__magnifications:
            logging.info("Querying magnification table..")

            body = RequestBody(attr="tem.AutoNormalizeEnabled", value=False)
            self.__client.call(method="set", body=body)

            saved_index = self.magnification_index
            previous_index = None
            index = 0
            while True:
                self.magnification_index = index
                index = self.magnification_index
                if index == previous_index:  # failed to _set new index
                    break
                self.__magnifications[self.magnification] = (index, self.magnification_range)
                previous_index = index
                index += 1
            # restore initial mag
            self.magnification_index = saved_index

            body = RequestBody(attr="tem.AutoNormalizeEnabled", value=True)
            self.__client.call(method="set", body=body)

            logging.info("Available magnifications: %s", self.__magnifications)

    @property
    def list_magnifications(self) -> Dict:
        """ List of available magnifications: mag -> (mag_index, submode). """
        return self.__magnifications

    @property
    def focus(self) -> float:
        """ Absolute focus value. (read/write)"""
        body = RequestBody(attr=self.__id + ".Focus", validator=float)
        return self.__client.call(method="get", body=body)

    @focus.setter
    def focus(self, value: float) -> None:
        if not (-1.0 <= value <= 1.0):
            raise ValueError("%s is outside of range -1.0 to 1.0" % value)

        body = RequestBody(attr=self.__id + ".Focus", value=value)
        self.__client.call(method="set", body=body)

    @property
    def magnification(self) -> int:
        """ The reference magnification value (screen up setting)."""
        body = RequestBody(attr=self.__id + ".Mode", validator=int)

        if self.__client.call(method="get", body=body) == ProjectionMode.IMAGING:
            body = RequestBody(attr=self.__id + ".Magnification", validator=float)
            return round(self.__client.call(method="get", body=body))
        else:
            raise RuntimeError(self.__err_msg)

    @magnification.setter
    def magnification(self, value: int) -> None:
        body = RequestBody(attr=self.__id + ".Mode", validator=int)

        if self.__client.call(method="get", body=body) == ProjectionMode.IMAGING:
            self.__find_magnifications()
            if value not in self.__magnifications:
                raise ValueError("Magnification %s not found in the table" % value)
            index = self.__magnifications[value][0]
            self.magnification_index = index
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def magnification_index(self) -> int:
        """ The magnification index. (read/write)"""
        body = RequestBody(attr=self.__id + ".MagnificationIndex", validator=int)
        return self.__client.call(method="get", body=body)

    @magnification_index.setter
    def magnification_index(self, value: int) -> None:
        body = RequestBody(attr=self.__id + ".MagnificationIndex", value=value)
        self.__client.call(method="set", body=body)

    @property
    def camera_length(self) -> float:
        """ The reference camera length in m (screen up setting). """
        body = RequestBody(attr=self.__id + ".Mode", validator=int)

        if self.__client.call(method="get", body=body) == ProjectionMode.DIFFRACTION:
            body = RequestBody(attr=self.__id + ".CameraLength", validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def camera_length_index(self) -> int:
        """ The camera length index. (read/write)"""
        body = RequestBody(attr=self.__id + ".CameraLengthIndex", validator=int)
        return self.__client.call(method="get", body=body)

    @camera_length_index.setter
    def camera_length_index(self, value: int) -> None:
        body = RequestBody(attr=self.__id + ".CameraLengthIndex", value=value)
        self.__client.call(method="set", body=body)

    @property
    def image_shift(self) -> Tuple:
        """ Image shift in um. (read/write)"""
        shx = RequestBody(attr=self.__id + ".ImageShift.X", validator=float)
        shy = RequestBody(attr=self.__id + ".ImageShift.Y", validator=float)

        x = self.__client.call(method="get", body=shx)
        y = self.__client.call(method="get", body=shy)

        return (x*1e6, y*1e6)

    @image_shift.setter
    def image_shift(self, values:Tuple) -> None:
        new_value = Vector(values[0] * 1e-6, values[1] * 1e-6)

        body = RequestBody(attr=self.__id + ".ImageShift", value=new_value)
        self.__client.call(method="set", body=body)

    @property
    def image_beam_shift(self) -> Tuple:
        """ Image shift with beam shift compensation in um. (read/write)"""
        bsx = RequestBody(attr=self.__id + ".ImageBeamShift.X", validator=float)
        bsy = RequestBody(attr=self.__id + ".ImageBeamShift.Y", validator=float)

        x = self.__client.call(method="get", body=bsx)
        y = self.__client.call(method="get", body=bsy)

        return (x*1e6, y*1e6)

    @image_beam_shift.setter
    def image_beam_shift(self, values: Tuple) -> None:
        new_value = Vector(values[0] * 1e-6, values[1] * 1e-6)

        body = RequestBody(attr=self.__id + ".ImageBeamShift", value=new_value)
        self.__client.call(method="set", body=body)

    @property
    def image_beam_tilt(self) -> Tuple:
        """ Beam tilt with diffraction shift compensation in mrad. (read/write)"""
        btx = RequestBody(attr=self.__id + ".ImageBeamTilt.X", validator=float)
        bty = RequestBody(attr=self.__id + ".ImageBeamTilt.Y", validator=float)

        x = self.__client.call(method="get", body=btx)
        y = self.__client.call(method="get", body=bty)

        return (x*1e3, y*1e3)

    @image_beam_tilt.setter
    def image_beam_tilt(self, values: Tuple) -> None:
        new_value = Vector(values[0] * 1e-3, values[1] * 1e-3)

        body = RequestBody(attr=self.__id + ".ImageBeamTilt", value=new_value)
        self.__client.call(method="set", body=body)

    @property
    def diffraction_shift(self) -> Tuple:
        """ Diffraction shift in mrad. (read/write)"""
        #TODO: 180/pi*value = approx number in TUI
        stigx = RequestBody(attr=self.__id + ".DiffractionShift.X", validator=float)
        stigy = RequestBody(attr=self.__id + ".DiffractionShift.Y", validator=float)

        x = self.__client.call(method="get", body=stigx)
        y = self.__client.call(method="get", body=stigy)

        return (x*1e3, y*1e3)

    @diffraction_shift.setter
    def diffraction_shift(self, values: Tuple) -> None:
        new_value = Vector(values[0] * 1e-3, values[1] * 1e-3)

        body = RequestBody(attr=self.__id + ".DiffractionShift", value=new_value)
        self.__client.call(method="set", body=body)

    @property
    def diffraction_stigmator(self) -> Tuple:
        """ Diffraction stigmator. (read/write)"""
        body = RequestBody(attr=self.__id + ".Mode", validator=int)

        if self.__client.call(method="get", body=body) == ProjectionMode.DIFFRACTION:
            stigx = RequestBody(attr=self.__id + ".DiffractionStigmator.X", validator=float)
            stigy = RequestBody(attr=self.__id + ".DiffractionStigmator.Y", validator=float)

            x = self.__client.call(method="get", body=stigx)
            y = self.__client.call(method="get", body=stigy)

            return (x, y)
        else:
            raise RuntimeError(self.__err_msg)

    @diffraction_stigmator.setter
    def diffraction_stigmator(self, values: Tuple) -> None:
        body = RequestBody(attr=self.__id + ".Mode", validator=int)

        if self.__client.call(method="get", body=body) == ProjectionMode.DIFFRACTION:
            new_value = Vector(*values)
            new_value.set_limits(-1.0, 1.0)

            body = RequestBody(attr=self.__id + ".DiffractionStigmator", value=new_value)
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def objective_stigmator(self) -> Tuple:
        """ Objective stigmator. (read/write)"""
        stigx = RequestBody(attr=self.__id + ".ObjectiveStigmator.X", validator=float)
        stigy = RequestBody(attr=self.__id + ".ObjectiveStigmator.Y", validator=float)

        x = self.__client.call(method="get", body=stigx)
        y = self.__client.call(method="get", body=stigy)

        return (x, y)

    @objective_stigmator.setter
    def objective_stigmator(self, values: Tuple) -> None:
        new_value = Vector(*values)
        new_value.set_limits(-1.0, 1.0)

        body = RequestBody(attr=self.__id + ".ObjectiveStigmator", value=new_value)
        self.__client.call(method="set", body=body)

    @property
    def defocus(self) -> float:
        """ Defocus value in um. (read/write)"""
        body = RequestBody(attr=self.__id + ".Defocus", validator=float)

        return self.__client.call(method="get", body=body) * 1e6

    @defocus.setter
    def defocus(self, value: float) -> None:
        body = RequestBody(attr=self.__id + ".Defocus", value=float(value) * 1e-6)
        self.__client.call(method="set", body=body)

    @property
    def mode(self) -> str:
        """ Main mode of the projection system (either imaging or diffraction). (read/write)"""
        body = RequestBody(attr=self.__id + ".Mode", validator=int)
        result = self.__client.call(method="get", body=body)

        return ProjectionMode(result).name

    @mode.setter
    def mode(self, mode: ProjectionMode) -> None:
        body = RequestBody(attr=self.__id + ".Mode", value=mode)
        self.__client.call(method="set", body=body)

    @property
    def detector_shift(self) -> str:
        """ Detector shift. (read/write)"""
        body = RequestBody(attr=self.__id + ".DetectorShift", validator=int)
        result = self.__client.call(method="get", body=body)

        return ProjectionDetectorShift(result).name

    @detector_shift.setter
    def detector_shift(self, value: ProjectionDetectorShift) -> None:
        body = RequestBody(attr=self.__id + ".DetectorShift", value=value)
        self.__client.call(method="set", body=body)

    @property
    def detector_shift_mode(self) -> str:
        """ Detector shift mode. (read/write)"""
        body = RequestBody(attr=self.__id + ".DetectorShiftMode", validator=int)
        result = self.__client.call(method="get", body=body)

        return ProjDetectorShiftMode(result).name

    @detector_shift_mode.setter
    def detector_shift_mode(self, value: ProjDetectorShiftMode) -> None:
        body = RequestBody(attr=self.__id + ".DetectorShiftMode", value=value)
        self.__client.call(method="set", body=body)

    @property
    def magnification_range(self) -> str:
        """ Submode of the projection system (either LM, M, SA, MH, LAD or D).
        The imaging submode can change when the magnification is changed.
        """
        body = RequestBody(attr=self.__id + ".SubMode", validator=int)
        result = self.__client.call(method="get", body=body)

        return ProjectionSubMode(result).name

    @property
    def image_rotation(self) -> float:
        """ The rotation of the image or diffraction pattern on the
        fluorescent screen with respect to the specimen. Units: mrad.
        """
        body = RequestBody(attr=self.__id + ".ImageRotation", validator=float)

        return self.__client.call(method="get", body=body) * 1e3

    @property
    def is_eftem_on(self) -> bool:
        """ Check if the EFTEM lens program setting is ON. """
        body = RequestBody(attr=self.__id + ".LensProgram", validator=int)
        result = self.__client.call(method="get", body=body)

        return LensProg(result) == LensProg.EFTEM

    def eftem_on(self) -> None:
        """ Switch on EFTEM. """
        body = RequestBody(attr=self.__id + ".LensProgram", value=LensProg.EFTEM)
        self.__client.call(method="set", body=body)

    def eftem_off(self) -> None:
        """ Switch off EFTEM. """
        body = RequestBody(attr=self.__id + ".LensProgram", value=LensProg.REGULAR)
        self.__client.call(method="set", body=body)

    def reset_defocus(self) -> None:
        """ Reset defocus value in the TEM user interface to zero.
        Does not change any lenses. """
        body = RequestBody(attr=self.__id + ".ResetDefocus()")
        self.__client.call(method="exec", body=body)
