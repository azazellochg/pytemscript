from functools import lru_cache
import logging
import time
from typing import Tuple, Union, List

from ..utils.misc import RequestBody
from ..utils.enums import FegState, HighTensionState, FegFlashingType
from .extras import Vector, SpecialObj


ERR_MSG_GUN1 = "Gun1 interface is not available. Requires TEM server 7.10+"


class GunObj(SpecialObj):
    """ Wrapper around Gun COM object specifically for the Gun1 interface. """
    def __init__(self, com_object):
        super().__init__(com_object)
        import comtypes.gen.TEMScripting as Ts
        if hasattr(Ts, "Gun1"):
            self.gun1 = self.com_object.QueryInterface(Ts.Gun1)
        else:
            self.gun1 = None

    def is_available(self) -> bool:
        """ Gun1 inherits from the Gun interface of the std scripting. """
        return self.gun1 is not None

    def get_hv_offset(self) -> float:
        if not self.is_available():
            raise NotImplementedError(ERR_MSG_GUN1)
        return self.gun1.HighVoltageOffset

    def set_hv_offset(self, value: float) -> None:
        if not self.is_available():
            raise NotImplementedError(ERR_MSG_GUN1)
        self.gun1.HighVoltageOffset = value

    def get_hv_offset_range(self) -> Tuple:
        if not self.is_available():
            raise NotImplementedError(ERR_MSG_GUN1)
        result = self.gun1.GetHighVoltageOffsetRange()
        return result[0], result[1]


class Gun:
    """ Gun functions. """
    __slots__ = ("__client", "__id", "__id_adv", "__err_msg_gun1", "__err_msg_cfeg")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem.Gun"
        self.__id_adv = "tem_adv.Source"
        self.__err_msg_cfeg = "Source/C-FEG interface is not available"

    @property
    @lru_cache(maxsize=1)
    def __has_gun1(self) -> bool:
        body = RequestBody(attr=self.__id,
                           obj_cls=GunObj,
                           obj_method="is_available",
                           validator=bool)
        return self.__client.call(method="exec_special", body=body)

    @property
    @lru_cache(maxsize=1)
    def __has_source(self) -> bool:
        body = RequestBody(attr=self.__id_adv + ".State", validator=bool)

        return self.__client.call(method="has", body=body)

    @property
    def shift(self) -> Vector:
        """ Gun shift. (read/write) """
        shx = RequestBody(attr=self.__id + ".Shift.X", validator=float)
        shy = RequestBody(attr=self.__id + ".Shift.Y", validator=float)

        x = self.__client.call(method="get", body=shx)
        y = self.__client.call(method="get", body=shy)

        return Vector(x, y)

    @shift.setter
    def shift(self, vector: Union[Vector, List[float], Tuple[float, float]]) -> None:
        value = Vector.convert_to(vector)
        value.set_limits(-1.0, 1.0)

        body = RequestBody(attr=self.__id + ".Shift", value=value)
        self.__client.call(method="set", body=body)

    @property
    def tilt(self) -> Vector:
        """ Gun tilt. (read/write) """
        tx = RequestBody(attr=self.__id + ".Tilt.X", validator=float)
        ty = RequestBody(attr=self.__id + ".Tilt.Y", validator=float)

        x = self.__client.call(method="get", body=tx)
        y = self.__client.call(method="get", body=ty)

        return Vector(x, y)

    @tilt.setter
    def tilt(self, vector: Union[Vector, List[float], Tuple[float, float]]) -> None:
        value = Vector.convert_to(vector)
        value.set_limits(-1.0, 1.0)

        body = RequestBody(attr=self.__id + ".Tilt", value=value)
        self.__client.call(method="set", body=body)

    @property
    def voltage_offset(self) -> float:
        """ High voltage offset. (read/write) """
        if self.__has_gun1:
            body = RequestBody(attr=self.__id,
                               obj_cls=GunObj,
                               obj_method="get_hv_offset",
                               validator=float)
            return self.__client.call(method="exec_special", body=body)
        else:
            raise NotImplementedError(ERR_MSG_GUN1)

    @voltage_offset.setter
    def voltage_offset(self, offset: float) -> None:
        if self.__has_gun1:
            body = RequestBody(attr=self.__id,
                               obj_cls=GunObj,
                               obj_method="set_hv_offset",
                               value=offset)
            self.__client.call(method="exec_special", body=body)
        else:
            raise NotImplementedError(ERR_MSG_GUN1)

    @property
    def feg_state(self) -> str:
        """ FEG emitter status (FegState enum). """
        if self.__has_source:
            body = RequestBody(attr=self.__id_adv + ".State", validator=int)
            result = self.__client.call(method="get", body=body)
            return FegState(result).name
        else:
            raise NotImplementedError(self.__err_msg_cfeg)

    @property
    def ht_state(self) -> str:
        """ High tension state: HighTensionState enum.

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
        if not (0.0 <= float(value) <= voltage_max):
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
    def voltage_offset_range(self) -> Tuple[float, float]:
        """ Returns the high voltage offset range. """
        if self.__has_gun1:
            body = RequestBody(attr=self.__id,
                               obj_cls=GunObj,
                               obj_method="get_hv_offset_range",
                               validator=tuple)
            return self.__client.call(method="exec_special", body=body)
        else:
            raise NotImplementedError(ERR_MSG_GUN1)

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
    def gun_lens(self) -> Tuple[int, int]:
        """ Returns coarse and fine gun lens index. Not available on systems with a monochromator. """
        if self.__has_source:
            coarse = RequestBody(attr=self.__id_adv + ".FocusIndex.Coarse", validator=int)
            fine = RequestBody(attr=self.__id_adv + ".FocusIndex.Fine", validator=int)
            return (self.__client.call(method="get", body=coarse),
                    self.__client.call(method="get", body=fine))
        else:
            raise NotImplementedError(self.__err_msg_cfeg)

    def do_flashing(self, flash_type: FegFlashingType) -> None:
        """ Perform cold FEG flashing.

        :param FegFlashingType flash_type:
        """
        if not self.__has_source:
            raise NotImplementedError(self.__err_msg_cfeg)

        if self.is_flashing_advised(flash_type):
            # Warning: lowT flashing can be done even if not advised
            doflash = RequestBody(attr=self.__id_adv + ".Flashing.PerformFlashing()",
                                  arg=flash_type)
            self.__client.call(method="exec", body=doflash)
        else:
            raise Warning("Flashing type %s is not advised" % flash_type)

    def is_flashing_advised(self, flash_type: FegFlashingType) -> bool:
        """ Check if cold FEG flashing is advised.

        :param FegFlashingType flash_type:
        """
        if not self.__has_source:
            raise NotImplementedError(self.__err_msg_cfeg)

        body = RequestBody(attr=self.__id_adv + ".Flashing.IsFlashingAdvised()",
                           arg=flash_type, validator=bool)
        return self.__client.call(method="exec", body=body)
