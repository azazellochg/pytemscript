class EnergyFilter:
    """ Energy filter controls. Requires advanced scripting. """
    __slots__ = ("__client", "__shortcut", "__has_ef", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__shortcut = "tem_adv.EnergyFilter"
        self.__has_ef = None
        self.__err_msg = "EnergyFilter interface is not available"

    @property
    def __adv_available(self) -> bool:
        if self.__has_ef is None:
            self.__has_ef = self.__client.has(self.__shortcut)
        return self.__has_ef

    def _check_range(self, attrname: str, value: float) -> None:
        vmin = self.__client.get(attrname + ".Begin")
        vmax = self.__client.get(attrname + ".End")
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
        self._check_range(self.__shortcut + ".Slit.WidthRange", width)
        self.__client.set(self.__shortcut + ".Slit.Width", float(width))
        if not self.__client.get(self.__shortcut + ".Slit.IsInserted"):
            self.__client.call(self.__shortcut + ".Slit.Insert()")

    def retract_slit(self) -> None:
        """ Retract energy slit. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        self.__client.call(self.__shortcut + ".Slit.Retract()")

    @property
    def slit_width(self) -> float:
        """ Returns energy slit width in eV. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        return self.__client.get(self.__shortcut + ".Slit.Width")

    @slit_width.setter
    def slit_width(self, value: float) -> None:
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        self._check_range(self.__shortcut + ".Slit.WidthRange", value)
        self.__client.set(self.__shortcut + ".Slit.Width", float(value))

    @property
    def ht_shift(self) -> float:
        """ Returns High Tension energy shift in eV. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        return self.__client.get(self.__shortcut + ".HighTensionEnergyShift.EnergyShift")

    @ht_shift.setter
    def ht_shift(self, value: float) -> None:
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        self._check_range(self.__shortcut + ".HighTensionEnergyShift.EnergyShiftRange", value)
        self.__client.set(self.__shortcut + ".HighTensionEnergyShift.EnergyShift", float(value))

    @property
    def zlp_shift(self) -> float:
        """ Returns Zero-Loss Peak (ZLP) energy shift in eV. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        return self.__client.get(self.__shortcut + ".ZeroLossPeakAdjustment.EnergyShift")

    @zlp_shift.setter
    def zlp_shift(self, value: float) -> None:
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        self._check_range(self.__shortcut + ".ZeroLossPeakAdjustment.EnergyShiftRange", value)
        self.__client.set(self.__shortcut + ".ZeroLossPeakAdjustment.EnergyShift", float(value))
