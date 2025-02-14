from typing import Dict
import logging

from ..utils.enums import ProjectionMode, ProjectionSubMode, ProjDetectorShiftMode, ProjectionDetectorShift, LensProg
from .extras import Vector


class Projection:
    """ Projection system functions. """
    __slots__ = ("__client", "__shortcut", "__err_msg", "__magnifications")

    def __init__(self, client):
        self.__client = client
        self.__shortcut = "tem.Projection"
        self.__err_msg = "Microscope is not in diffraction mode"
        self.__magnifications = {}
        self.__find_magnifications()

    def __find_magnifications(self) -> None:
        if not self.__magnifications:
            logging.info("Querying magnification table..")
            self.__client.set("tem.AutoNormalizeEnabled", False)
            saved_index = self.magnification_index
            previous_index = None
            index = 0
            while True:
                self.magnification_index = index
                index = self.magnification_index
                if index == previous_index:  # failed to set new index
                    break
                self.__magnifications[self.magnification] = (index, self.magnification_range)
                previous_index = index
                index += 1
            # restore initial mag
            self.magnification_index = saved_index
            self.__client.set("tem.AutoNormalizeEnabled", True)
            logging.info("Available magnifications: %s", self.__magnifications)

    @property
    def list_magnifications(self) -> Dict:
        """ List of available magnifications: mag -> (mag_index, submode). """
        return self.__magnifications

    @property
    def focus(self) -> float:
        """ Absolute focus value. (read/write)"""
        return self.__client.get(self.__shortcut + ".Focus")

    @focus.setter
    def focus(self, value: float) -> None:
        if not (-1.0 <= value <= 1.0):
            raise ValueError("%s is outside of range -1.0 to 1.0" % value)

        self.__client.set(self.__shortcut + ".Focus", float(value))

    @property
    def magnification(self) -> int:
        """ The reference magnification value (screen up setting)."""
        if self.__client.get(self.__shortcut + ".Mode") == ProjectionMode.IMAGING:
            return round(self.__client.get(self.__shortcut + ".Magnification"))
        else:
            raise RuntimeError(self.__err_msg)

    @magnification.setter
    def magnification(self, value: int) -> None:
        if self.__client.get(self.__shortcut + ".Mode") == ProjectionMode.IMAGING:
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
        return self.__client.get(self.__shortcut + ".MagnificationIndex")

    @magnification_index.setter
    def magnification_index(self, value: int) -> None:
        self.__client.set(self.__shortcut + ".MagnificationIndex", value)

    @property
    def camera_length(self) -> float:
        """ The reference camera length in m (screen up setting). """
        if self.__client.get(self.__shortcut + ".Mode") == ProjectionMode.DIFFRACTION:
            return self.__client.get(self.__shortcut + ".CameraLength")
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def camera_length_index(self) -> int:
        """ The camera length index. (read/write)"""
        return self.__client.get(self.__shortcut + ".CameraLengthIndex")

    @camera_length_index.setter
    def camera_length_index(self, value: int) -> None:
        self.__client.set(self.__shortcut + ".CameraLengthIndex", value)

    @property
    def image_shift(self) -> tuple:
        """ Image shift in um. (read/write)"""
        return (self.__client.get(self.__shortcut + ".ImageShift.X") * 1e6,
                self.__client.get(self.__shortcut + ".ImageShift.Y") * 1e6)

    @image_shift.setter
    def image_shift(self, values:tuple) -> None:
        new_value = Vector(values[0] * 1e-6, values[1] * 1e-6)
        self.__client.set(self.__shortcut + ".ImageShift", new_value)

    @property
    def image_beam_shift(self) -> tuple:
        """ Image shift with beam shift compensation in um. (read/write)"""
        return (self.__client.get(self.__shortcut + ".ImageBeamShift.X") * 1e6,
                self.__client.get(self.__shortcut + ".ImageBeamShift.Y") * 1e6)

    @image_beam_shift.setter
    def image_beam_shift(self, values: tuple) -> None:
        new_value = Vector(values[0] * 1e-6, values[1] * 1e-6)
        self.__client.set(self.__shortcut + ".ImageBeamShift", new_value)

    @property
    def image_beam_tilt(self) -> tuple:
        """ Beam tilt with diffraction shift compensation in mrad. (read/write)"""
        return (self.__client.get(self.__shortcut + ".ImageBeamTilt.X") * 1e3,
                self.__client.get(self.__shortcut + ".ImageBeamTilt.Y") * 1e3)

    @image_beam_tilt.setter
    def image_beam_tilt(self, values: tuple) -> None:
        new_value = Vector(values[0] * 1e-3, values[1] * 1e-3)
        self.__client.set(self.__shortcut + ".ImageBeamTilt", new_value)

    @property
    def diffraction_shift(self) -> tuple:
        """ Diffraction shift in mrad. (read/write)"""
        #TODO: 180/pi*value = approx number in TUI
        return (self.__client.get(self.__shortcut + ".DiffractionShift.X") * 1e3,
                self.__client.get(self.__shortcut + ".DiffractionShift.Y") * 1e3)

    @diffraction_shift.setter
    def diffraction_shift(self, values: tuple) -> None:
        new_value = Vector(values[0] * 1e-3, values[1] * 1e-3)
        self.__client.set(self.__shortcut + ".DiffractionShift", new_value)

    @property
    def diffraction_stigmator(self) -> tuple:
        """ Diffraction stigmator. (read/write)"""
        if self.__client.get(self.__shortcut + ".Mode") == ProjectionMode.DIFFRACTION:
            return (self.__client.get(self.__shortcut + ".DiffractionStigmator.X"),
                    self.__client.get(self.__shortcut + ".DiffractionStigmator.Y"))
        else:
            raise RuntimeError(self.__err_msg)

    @diffraction_stigmator.setter
    def diffraction_stigmator(self, values: tuple) -> None:
        if self.__client.get(self.__shortcut + ".Mode") == ProjectionMode.DIFFRACTION:
            new_value = Vector(*values)
            new_value.set_limits(-1.0, 1.0)
            self.__client.set(self.__shortcut + ".DiffractionStigmator", new_value)
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def objective_stigmator(self) -> tuple:
        """ Objective stigmator. (read/write)"""
        return (self.__client.get(self.__shortcut + ".ObjectiveStigmator.X"),
                self.__client.get(self.__shortcut + ".ObjectiveStigmator.Y"))

    @objective_stigmator.setter
    def objective_stigmator(self, values: tuple) -> None:
        new_value = Vector(*values)
        new_value.set_limits(-1.0, 1.0)
        self.__client.set(self.__shortcut + ".ObjectiveStigmator", new_value)

    @property
    def defocus(self) -> float:
        """ Defocus value in um. (read/write)"""
        return self.__client.get(self.__shortcut + ".Defocus") * 1e6

    @defocus.setter
    def defocus(self, value: float) -> None:
        self.__client.set(self.__shortcut + ".Defocus", float(value) * 1e-6)

    @property
    def mode(self) -> str:
        """ Main mode of the projection system (either imaging or diffraction). (read/write)"""
        return ProjectionMode(self.__client.get(self.__shortcut + ".Mode")).name

    @mode.setter
    def mode(self, mode: ProjectionMode) -> None:
        self.__client.set(self.__shortcut + ".Mode", mode)

    @property
    def detector_shift(self) -> str:
        """ Detector shift. (read/write)"""
        return ProjectionDetectorShift(self.__client.get(self.__shortcut + ".DetectorShift")).name

    @detector_shift.setter
    def detector_shift(self, value: ProjectionDetectorShift) -> None:
        self.__client.set(self.__shortcut + ".DetectorShift", value)

    @property
    def detector_shift_mode(self) -> str:
        """ Detector shift mode. (read/write)"""
        return ProjDetectorShiftMode(self.__client.get(self.__shortcut + ".DetectorShiftMode")).name

    @detector_shift_mode.setter
    def detector_shift_mode(self, value: ProjDetectorShiftMode) -> None:
        self.__client.set(self.__shortcut + ".DetectorShiftMode", value)

    @property
    def magnification_range(self) -> str:
        """ Submode of the projection system (either LM, M, SA, MH, LAD or D).
        The imaging submode can change when the magnification is changed.
        """
        return ProjectionSubMode(self.__client.get(self.__shortcut + ".SubMode")).name

    @property
    def image_rotation(self) -> float:
        """ The rotation of the image or diffraction pattern on the
        fluorescent screen with respect to the specimen. Units: mrad.
        """
        return self.__client.get(self.__shortcut + ".ImageRotation") * 1e3

    @property
    def is_eftem_on(self) -> bool:
        """ Check if the EFTEM lens program setting is ON. """
        return LensProg(self.__client.get(self.__shortcut + ".LensProgram")) == LensProg.EFTEM

    def eftem_on(self) -> None:
        """ Switch on EFTEM. """
        self.__client.set(self.__shortcut + ".LensProgram", LensProg.EFTEM)

    def eftem_off(self) -> None:
        """ Switch off EFTEM. """
        self.__client.set(self.__shortcut + ".LensProgram", LensProg.REGULAR)

    def reset_defocus(self) -> None:
        """ Reset defocus value in the TEM user interface to zero.
        Does not change any lenses. """
        self.__client.call(self.__shortcut + ".ResetDefocus()")
