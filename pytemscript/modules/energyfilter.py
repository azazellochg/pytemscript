from ..utils.misc import RequestBody


class EnergyFilter:
    """ Energy filter controls. Requires advanced scripting. """
    __slots__ = ("__client", "__id", "__has_ef", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem_adv.EnergyFilter"
        self.__has_ef = None
        self.__err_msg = "EnergyFilter interface is not available"

    @property
    def __adv_available(self) -> bool:
        if self.__has_ef is None:
            body = RequestBody(attr="tem.Gun1", validator=bool)
            self.__has_ef = self.__client.call(method="has", body=body)
        return self.__has_ef

    def _check_range(self, attrname: str, value: float) -> None:
        vmin = RequestBody(attr=attrname + ".Begin", validator=float)
        vmax = RequestBody(attr=attrname + ".End", validator=float)

        vmin = self.__client.call(method="get", body=vmin)
        vmax = self.__client.call(method="get", body=vmax)

        if not (vmin <= float(value) <= vmax):
            raise ValueError("Value is outside of allowed "
                             "range: %0.3f - %0.3f" % (vmin, vmax))

    def insert_slit(self, width: float) -> None:
        """ Insert energy slit.

        :param width: Slit width in eV
        :type width: float
        """
        if not self.__adv_available:
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
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)

        body = RequestBody(attr=self.__id + ".Slit.Retract()")
        self.__client.call(method="exec", body=body)

    @property
    def slit_width(self) -> float:
        """ Returns energy slit width in eV. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)

        body = RequestBody(attr=self.__id + ".Slit.Width", validator=float)
        return self.__client.call(method="get", body=body)

    @slit_width.setter
    def slit_width(self, value: float) -> None:
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)

        self._check_range(self.__id + ".Slit.WidthRange", value)
        body = RequestBody(attr=self.__id + ".Slit.Width", value=value)
        self.__client.call(method="set", body=body)

    @property
    def ht_shift(self) -> float:
        """ Returns High Tension energy shift in eV. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)

        body = RequestBody(attr=self.__id + ".HighTensionEnergyShift.EnergyShift", validator=float)
        return self.__client.call(method="get", body=body)

    @ht_shift.setter
    def ht_shift(self, value: float) -> None:
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)

        self._check_range(self.__id + ".HighTensionEnergyShift.EnergyShiftRange", value)
        body = RequestBody(attr=self.__id + ".HighTensionEnergyShift.EnergyShift", value=value)
        self.__client.call(method="set", body=body)

    @property
    def zlp_shift(self) -> float:
        """ Returns Zero-Loss Peak (ZLP) energy shift in eV. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)

        body = RequestBody(attr=self.__id + ".ZeroLossPeakAdjustment.EnergyShift", validator=float)
        return self.__client.call(method="get", body=body)

    @zlp_shift.setter
    def zlp_shift(self, value: float) -> None:
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)

        self._check_range(self.__id + ".ZeroLossPeakAdjustment.EnergyShiftRange", value)
        body = RequestBody(attr=self.__id + ".ZeroLossPeakAdjustment.EnergyShift", value=value)
        self.__client.call(method="set", body=body)
