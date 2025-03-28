import logging
from typing import Union

from ..utils.misc import RequestBody
from ..utils.enums import ProjectionNormalization, IlluminationNormalization, InstrumentMode
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
    def instrument_mode(self) -> str:
        """ Current instrument mode: TEM or STEM (InstrumentMode enum). """
        body = RequestBody(attr="tem.InstrumentModeControl.InstrumentMode", validator=int)
        result = self.__client.call(method="get", body=body)

        return InstrumentMode(result).name

    @property
    def screen_current(self) -> float:
        """ The current measured on the fluorescent screen (units: nanoAmperes). """
        body = RequestBody(attr="tem.Camera.ScreenCurrent", validator=float)

        return self.__client.call(method="get", body=body) * 1e9

    @property
    def is_beam_blanked(self) -> bool:
        """ Status of the beam blanker. """
        body = RequestBody(attr="tem.Illumination.BeamBlanked", validator=bool)

        return self.__client.call(method="get", body=body)

    @property
    def is_shutter_override_on(self) -> bool:
        """ Determines the state of the shutter override function.

        WARNING: Do not leave the Shutter override on when stopping the script.
        The microscope operator will be unable to have a beam come down and has
        no separate way of seeing that it is blocked by the closed microscope shutter.
        """
        body = RequestBody(attr="tem.BlankerShutter.ShutterOverrideOn", validator=bool)

        return self.__client.call(method="get", body=body)

    @property
    def is_autonormalize_on(self) -> bool:
        """ Status of the automatic normalization procedures performed by
        the TEM microscope. Normally they are active, but for scripting it can be
        convenient to disable them temporarily.
        """
        body = RequestBody(attr="tem.AutoNormalizeEnabled", validator=bool)

        return self.__client.call(method="get", body=body)

    def beam_blank(self) -> None:
        """ Activates the beam blanker. """
        body = RequestBody(attr="tem.Illumination.BeamBlanked", value=True)
        self.__client.call(method="set", body=body)

        logging.warning("Falcon protector might delay blanker response")

    def beam_unblank(self) -> None:
        """ Deactivates the beam blanker. """
        body = RequestBody(attr="tem.Illumination.BeamBlanked", value=False)
        self.__client.call(method="set", body=body)

        logging.warning("Falcon protector might delay blanker response")

    def normalize_all(self) -> None:
        """ Normalize all lenses. """
        body = RequestBody(attr="tem.NormalizeAll()")
        self.__client.call(method="exec", body=body)

    def normalize(self, mode: Union[ProjectionNormalization, IlluminationNormalization]) -> None:
        """ Normalize condenser or projection lens system.

        :param mode:
        :type mode: ProjectionNormalization or IlluminationNormalization
        """
        if mode in ProjectionNormalization:
            body = RequestBody(attr="tem.Projection.Normalize()", arg=mode)
            self.__client.call(method="exec", body=body)
        elif mode in IlluminationNormalization:
            body = RequestBody(attr="tem.Illumination.Normalize()", arg=mode)
            self.__client.call(method="exec", body=body)
        else:
            raise ValueError("Unknown normalization mode: %s" % mode)
