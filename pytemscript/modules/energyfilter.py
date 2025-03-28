from functools import lru_cache

from ..utils.misc import RequestBody


class EnergyFilter:
    """ Energy filter controls. Requires advanced scripting. """
    __slots__ = ("__client", "__id", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem_adv.EnergyFilter"
        self.__err_msg = "EnergyFilter advanced interface is not available. Requires TEM server 7.8+"

    @property
    @lru_cache(maxsize=1)
    def __has_ef(self) -> bool:
        body = RequestBody(attr=self.__id, validator=bool)

        return self.__client.call(method="has", body=body)

    def _check_range(self, attrname: str, value: float) -> None:
        start = RequestBody(attr=attrname + ".Begin", validator=float)
        end = RequestBody(attr=attrname + ".End", validator=float)

        vmin = self.__client.call(method="get", body=start)
        vmax = self.__client.call(method="get", body=end)

        if not (vmin <= float(value) <= vmax):
            raise ValueError("Value is outside of allowed "
                             "range: %0.3f - %0.3f" % (vmin, vmax))

    def insert_slit(self, width: float) -> None:
        """ Insert energy slit.

        :param float width: Slit width in eV
        """
        if not self.__has_ef:
            raise NotImplementedError(self.__err_msg)

        self._check_range(self.__id + ".Slit.WidthRange", width)
        body = RequestBody(attr=self.__id + ".Slit.Width", value=width)
        self.__client.call(method="set", body=body)

        ins = RequestBody(attr=self.__id + ".Slit.IsInserted", validator=bool)
        if not self.__client.call(method="get", body=ins):
            body = RequestBody(attr=self.__id + ".Slit.Insert()")
            self.__client.call(method="exec", body=body)

    def retract_slit(self) -> None:
        """ Retract energy slit. """
        if not self.__has_ef:
            raise NotImplementedError(self.__err_msg)

        body = RequestBody(attr=self.__id + ".Slit.Retract()")
        self.__client.call(method="exec", body=body)

    @property
    def slit_width(self) -> float:
        """ Energy slit width in eV. (read/write) """
        if not self.__has_ef:
            raise NotImplementedError(self.__err_msg)

        body = RequestBody(attr=self.__id + ".Slit.Width", validator=float)
        return self.__client.call(method="get", body=body)

    @slit_width.setter
    def slit_width(self, value: float) -> None:
        if not self.__has_ef:
            raise NotImplementedError(self.__err_msg)

        self._check_range(self.__id + ".Slit.WidthRange", value)
        body = RequestBody(attr=self.__id + ".Slit.Width", value=value)
        self.__client.call(method="set", body=body)

    @property
    def ht_shift(self) -> float:
        """ High Tension energy shift in eV. (read/write) """
        if not self.__has_ef:
            raise NotImplementedError(self.__err_msg)

        body = RequestBody(attr=self.__id + ".HighTensionEnergyShift.EnergyShift", validator=float)
        return self.__client.call(method="get", body=body)

    @ht_shift.setter
    def ht_shift(self, value: float) -> None:
        if not self.__has_ef:
            raise NotImplementedError(self.__err_msg)

        self._check_range(self.__id + ".HighTensionEnergyShift.EnergyShiftRange", value)
        body = RequestBody(attr=self.__id + ".HighTensionEnergyShift.EnergyShift", value=value)
        self.__client.call(method="set", body=body)

    @property
    def zlp_shift(self) -> float:
        """ Zero-Loss Peak (ZLP) energy shift in eV. (read/write) """
        if not self.__has_ef:
            raise NotImplementedError(self.__err_msg)

        body = RequestBody(attr=self.__id + ".ZeroLossPeakAdjustment.EnergyShift", validator=float)
        return self.__client.call(method="get", body=body)

    @zlp_shift.setter
    def zlp_shift(self, value: float) -> None:
        if not self.__has_ef:
            raise NotImplementedError(self.__err_msg)

        self._check_range(self.__id + ".ZeroLossPeakAdjustment.EnergyShiftRange", value)
        body = RequestBody(attr=self.__id + ".ZeroLossPeakAdjustment.EnergyShift", value=value)
        self.__client.call(method="set", body=body)
