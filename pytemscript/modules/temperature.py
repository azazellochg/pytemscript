class Temperature:
    """ LN dewars and temperature controls. """
    __slots__ = ("__client", "__has_tmpctrl", "__has_tmpctrl_adv",
                 "__shortcut", "__shortcut2", "__err_msg", "__err_msg_adv")

    def __init__(self, client):
        self.__client = client
        self.__has_tmpctrl = None
        self.__has_tmpctrl_adv = None
        self.__shortcut = "tem.TemperatureControl"
        self.__shortcut2 = "tem_adv.TemperatureControl.AutoloaderCompartment"
        self.__err_msg = "TemperatureControl is not available"
        self.__err_msg_adv = "This function is not available in your advanced scripting interface."
    
    @property    
    def __std_available(self) -> bool:
        if self.__has_tmpctrl is None:
            self.__has_tmpctrl = self.__client.has(self.__shortcut)
        return self.__has_tmpctrl

    @property
    def __adv_available(self) -> bool:
        if self.__has_tmpctrl_adv is None:
            self.__has_tmpctrl_adv = self.__client.has("tem_adv.TemperatureControl")
        return self.__has_tmpctrl_adv

    @property
    def is_available(self) -> bool:
        """ Status of the temperature control. Should be always False on Tecnai instruments. """
        if self.__std_available:
            return self.__client.has(self.__shortcut + ".TemperatureControlAvailable")
        else:
            return False

    def force_refill(self) -> None:
        """ Forces LN refill if the level is below 70%, otherwise returns an error.
        Note: this function takes considerable time to execute.
        """
        if self.__std_available:
            self.__client.call(self.__shortcut + ".ForceRefill()")
        elif self.__adv_available:
            return self.__client.call("tem_adv.TemperatureControl.RefillAllDewars()")
        else:
            raise NotImplementedError(self.__err_msg)

    def dewar_level(self, dewar) -> float:
        """ Returns the LN level (%) in a dewar.

        :param dewar: Dewar name (RefrigerantDewar enum)
        :type dewar: IntEnum
        """
        if self.__std_available:
            return self.__client.call(self.__shortcut + ".RefrigerantLevel()", dewar)
        else:
            raise NotImplementedError(self.__err_msg)

    @property
    def is_dewar_filling(self) -> bool:
        """ Returns TRUE if any of the dewars is currently busy filling. """
        if self.__std_available:
            return bool(self.__client.get(self.__shortcut + ".DewarsAreBusyFilling"))
        elif self.__adv_available:
            return bool(self.__client.get("tem_adv.TemperatureControl.IsAnyDewarFilling"))
        else:
            raise NotImplementedError(self.__err_msg)

    @property
    def dewars_time(self) -> float:
        """ Returns remaining time (seconds) until the next dewar refill.
        Returns -1 if no refill is scheduled (e.g. All room temperature, or no
        dewar present).
        """
        # TODO: check if returns -60 at room temperature
        if self.__std_available:
            return self.__client.get(self.__shortcut + ".DewarsRemainingTime")
        else:
            raise NotImplementedError(self.__err_msg)

    @property
    def temp_docker(self) -> float:
        """ Returns Docker temperature in Kelvins. """
        if self.__adv_available:
            return self.__client.get(self.__shortcut2 + ".DockerTemperature")
        else:
            raise NotImplementedError(self.__err_msg_adv)

    @property
    def temp_cassette(self) -> float:
        """ Returns Cassette gripper temperature in Kelvins. """
        if self.__adv_available:
            return self.__client.get(self.__shortcut2 + ".CassetteTemperature")
        else:
            raise NotImplementedError(self.__err_msg_adv)

    @property
    def temp_cartridge(self) -> float:
        """ Returns Cartridge gripper temperature in Kelvins. """
        if self.__adv_available:
            return self.__client.get(self.__shortcut2 + ".CartridgeTemperature")
        else:
            raise NotImplementedError(self.__err_msg_adv)

    @property
    def temp_holder(self) -> float:
        """ Returns Holder temperature in Kelvins. """
        if self.__adv_available:
            return self.__client.get(self.__shortcut2 + ".HolderTemperature")
        else:
            raise NotImplementedError(self.__err_msg_adv)
