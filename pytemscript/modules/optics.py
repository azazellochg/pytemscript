import logging

from ..utils.enums import ProjectionNormalization, IlluminationNormalization
from .illumination import Illumination
from .projection import Projection


class Optics:
    """ Projection, Illumination functions. """
    __slots__ = ("__client", "illumination", "projection")

    def __init__(self, client, condenser_type):
        self.__client = client
        self.illumination = Illumination(client, condenser_type)
        self.projection = Projection(client)

    @property
    def screen_current(self) -> float:
        """ The current measured on the fluorescent screen (units: nanoAmperes). """
        return self.__client.get("tem.Camera.ScreenCurrent") * 1e9

    @property
    def is_beam_blanked(self) -> bool:
        """ Status of the beam blanker. """
        return self.__client.get("tem.Illumination.BeamBlanked")

    @property
    def is_shutter_override_on(self) -> bool:
        """ Determines the state of the shutter override function.
        WARNING: Do not leave the Shutter override on when stopping the script.
        The microscope operator will be unable to have a beam come down and has
        no separate way of seeing that it is blocked by the closed microscope shutter.
        """
        return self.__client.get("tem.BlankerShutter.ShutterOverrideOn")

    @property
    def is_autonormalize_on(self) -> bool:
        """ Status of the automatic normalization procedures performed by
        the TEM microscope. Normally they are active, but for scripting it can be
        convenient to disable them temporarily.
        """
        return self.__client.get("tem.AutoNormalizeEnabled")

    def beam_blank(self) -> None:
        """ Activates the beam blanker. """
        self.__client.set("tem.Illumination.BeamBlanked", True)
        logging.warning("Falcon protector might delay blanker response")

    def beam_unblank(self) -> None:
        """ Deactivates the beam blanker. """
        self.__client.set("tem.Illumination.BeamBlanked", False)
        logging.warning("Falcon protector might delay blanker response")

    def normalize_all(self) -> None:
        """ Normalize all lenses. """
        self.__client.call("tem.NormalizeAll()")

    def normalize(self, mode) -> None:
        """ Normalize condenser or projection lens system.
        :param mode: Normalization mode (ProjectionNormalization or IlluminationNormalization enum)
        :type mode: IntEnum
        """
        if mode in ProjectionNormalization:
            self.__client.call("tem.Projection.Normalize()", mode)
        elif mode in IlluminationNormalization:
            self.__client.call("tem.Illumination.Normalize()", mode)
        else:
            raise ValueError("Unknown normalization mode: %s" % mode)
