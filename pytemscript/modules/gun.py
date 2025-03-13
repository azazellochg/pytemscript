from functools import lru_cache
import logging
import time
from typing import Tuple

from ..utils.misc import RequestBody
from ..utils.enums import FegState, HighTensionState, FegFlashingType
from .extras import Vector


class Gun:
    """ Gun functions. """
    __slots__ = ("__client", "__id", "__id_adv", "__err_msg_gun1", "__err_msg_cfeg")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem.Gun"
        self.__id_adv = "tem_adv.Source"
        self.__err_msg_gun1 = "Gun1 interface is not available. Requires TEM server 7.10+"
        self.__err_msg_cfeg = "Source/C-FEG interface is not available"

    @property
    @lru_cache(maxsize=1)
    def __has_gun1(self) -> bool:
        body = RequestBody(attr="tem.Gun1", validator=bool)

        return self.__client.call(method="has", body=body)

    @property
    @lru_cache(maxsize=1)
    def __has_source(self) -> bool:
        body = RequestBody(attr=self.__id_adv + ".State", validator=bool)

        return self.__client.call(method="has", body=body)

    @property
    def shift(self) -> Vector:
        """ Gun shift. (read/write)"""
        shx = RequestBody(attr=self.__id + ".Shift.X", validator=float)
        shy = RequestBody(attr=self.__id + ".Shift.Y", validator=float)

        x = self.__client.call(method="get", body=shx)
        y = self.__client.call(method="get", body=shy)

        return Vector(x, y)

    @shift.setter
    def shift(self, vector: Vector) -> None:
        vector.set_limits(-1.0, 1.0)

        body = RequestBody(attr=self.__id + ".Shift", value=vector)
        self.__client.call(method="set", body=body)

    @property
    def tilt(self) -> Vector:
        """ Gun tilt. (read/write)"""
        tx = RequestBody(attr=self.__id + ".Tilt.X", validator=float)
        ty = RequestBody(attr=self.__id + ".Tilt.Y", validator=float)

        x = self.__client.call(method="get", body=tx)
        y = self.__client.call(method="get", body=ty)

        return Vector(x, y)

    @tilt.setter
    def tilt(self, vector: Vector) -> None:
        vector.set_limits(-1.0, 1.0)

        body = RequestBody(attr=self.__id + ".Tilt", value=vector)
        self.__client.call(method="set", body=body)

    @property
    def voltage_offset(self) -> float:
        """ High voltage offset. (read/write)"""
        if self.__has_gun1:
            body = RequestBody(attr="tem.Gun1.HighVoltageOffset", validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg_gun1)

    @voltage_offset.setter
    def voltage_offset(self, offset: float) -> None:
        if self.__has_gun1:
            body = RequestBody(attr="tem.Gun1.HighVoltageOffset", value=offset)
            self.__client.call(method="set", body=body)
        else:
            raise NotImplementedError(self.__err_msg_gun1)

    @property
    def feg_state(self) -> str:
        """ FEG emitter status. """
        if self.__has_source:
            body = RequestBody(attr=self.__id_adv + ".State", validator=int)
            result = self.__client.call(method="get", body=body)
            return FegState(result).name
        else:
            raise NotImplementedError(self.__err_msg_cfeg)

    @property
    def ht_state(self) -> str:
        """ High tension state: on, off or disabled.
        Disabling/enabling can only be done via the button on the
        system on/off-panel, not via script. When switching on
        the high tension, this function cannot check if and
        when the set value is actually reached. (read/write)
        """
        body = RequestBody(attr=self.__id + ".HTState", validator=int)
        result = self.__client.call(method="get", body=body)

        return HighTensionState(result).name

    @ht_state.setter
    def ht_state(self, value: HighTensionState) -> None:
        body = RequestBody(attr=self.__id + ".HTState", value=value)
        self.__client.call(method="set", body=body)

    @property
    def voltage(self) -> float:
        """ The value of the HT setting as displayed in the TEM user
        interface. Units: kVolts. (read/write)
        """
        body = RequestBody(attr=self.__id + ".HTState", validator=int)
        state = self.__client.call(method="get", body=body)

        if state == HighTensionState.ON:
            body = RequestBody(attr=self.__id + ".HTValue", validator=float)
            return self.__client.call(method="get", body=body) * 1e-3
        else:
            return 0.0

    @voltage.setter
    def voltage(self, value: float) -> None:
        voltage_max = self.voltage_max
        if not (0.0 <= value <= voltage_max):
            raise ValueError("%s is outside of range 0.0-%s" % (value, voltage_max))

        body = RequestBody(attr=self.__id + ".HTValue", value=float(value) * 1000)
        self.__client.call(method="set", body=body)

        while True:
            body = RequestBody(attr=self.__id + ".HTValue", validator=float)
            if self.__client.call(method="get", body=body) == float(value) * 1000:
                logging.info("Changing HT voltage complete.")
                break
            else:
                time.sleep(10)

    @property
    def voltage_max(self) -> float:
        """ The maximum possible value of the HT on this microscope. Units: kVolts. """
        body = RequestBody(attr=self.__id + ".HTMaxValue", validator=float)
        return self.__client.call(method="get", body=body) * 1e-3

    @property
    def voltage_offset_range(self):
        """ Returns the high voltage offset range. """
        if self.__has_gun1:
            #TODO: this is a function?
            body = RequestBody(attr="tem.Gun1.GetHighVoltageOffsetRange()")
            return self.__client.call(method="exec", body=body)
        else:
            raise NotImplementedError(self.__err_msg_gun1)

    @property
    def beam_current(self) -> float:
        """ Returns the C-FEG beam current in nanoAmperes. """
        if self.__has_source:
            body = RequestBody(attr=self.__id_adv + ".BeamCurrent", validator=float)
            return self.__client.call(method="get", body=body) * 1e9
        else:
            raise NotImplementedError(self.__err_msg_cfeg)

    @property
    def extractor_voltage(self) -> float:
        """ Returns the extractor voltage. """
        if self.__has_source:
            body = RequestBody(attr=self.__id_adv + ".ExtractorVoltage", validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg_cfeg)

    @property
    def focus_index(self) -> Tuple[int, int]:
        """ Returns coarse and fine gun lens index. """
        if self.__has_source:
            coarse = RequestBody(attr=self.__id_adv + ".FocusIndex.Coarse", validator=int)
            fine = RequestBody(attr=self.__id_adv + ".FocusIndex.Fine", validator=int)
            return (self.__client.call(method="get", body=coarse),
                    self.__client.call(method="get", body=fine))
        else:
            raise NotImplementedError(self.__err_msg_cfeg)

    def do_flashing(self, flash_type: FegFlashingType) -> None:
        """ Perform cold FEG flashing.

        :param flash_type: FEG flashing type (FegFlashingType enum)
        :type flash_type: IntEnum
        """
        if not self.__has_source:
            raise NotImplementedError(self.__err_msg_cfeg)

        body = RequestBody(attr=self.__id_adv + ".Flashing.IsFlashingAdvised()",
                           arg=flash_type, validator=bool)
        if self.__client.call(method="exec", body=body):
            # Warning: lowT flashing can be done even if not advised
            doflash = RequestBody(attr=self.__id_adv + ".Flashing.PerformFlashing()",
                                  arg=flash_type)
            self.__client.call(method="exec", body=doflash)
        else:
            raise Warning("Flashing type %s is not advised" % flash_type)
