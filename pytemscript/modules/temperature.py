from ..utils.misc import RequestBody


class Temperature:
    """ LN dewars and temperature controls. """
    __slots__ = ("__client", "__has_tmpctrl", "__has_tmpctrl_adv",
                 "__id", "__id_adv", "__err_msg", "__err_msg_adv")

    def __init__(self, client):
        self.__client = client
        self.__has_tmpctrl = None
        self.__has_tmpctrl_adv = None
        self.__id = "tem.TemperatureControl"
        self.__id_adv = "tem_adv.TemperatureControl"
        self.__err_msg = "TemperatureControl is not available"
        self.__err_msg_adv = "This function is not available in your advanced scripting interface."
    
    @property    
    def __std_available(self) -> bool:
        if self.__has_tmpctrl is None:
            body = RequestBody(attr=self.__id, validator=bool)
            self.__has_tmpctrl = self.__client.call(method="has", body=body)

        return self.__has_tmpctrl

    @property
    def __adv_available(self) -> bool:
        if self.__has_tmpctrl_adv is None:
            body = RequestBody(attr=self.__id_adv, validator=bool)
            self.__has_tmpctrl_adv = self.__client.call(method="has", body=body)

        return self.__has_tmpctrl_adv

    @property
    def is_available(self) -> bool:
        """ Status of the temperature control. Should be always False on Tecnai instruments. """
        if self.__std_available:
            body = RequestBody(attr=self.__id + ".TemperatureControlAvailable", validator=bool)
            return self.__client.call(method="has", body=body)
        else:
            return False

    def force_refill(self) -> None:
        """ Forces LN refill if the level is below 70%, otherwise returns an error.
        Note: this function takes considerable time to execute.
        """
        if self.__std_available:
            body = RequestBody(attr=self.__id + ".ForceRefill()")
            self.__client.call(method="exec", body=body)
        elif self.__adv_available:
            body = RequestBody(attr=self.__id_adv + ".RefillAllDewars()")
            self.__client.call(method="exec", body=body)
        else:
            raise NotImplementedError(self.__err_msg)

    def dewar_level(self, dewar) -> float:
        """ Returns the LN level (%) in a dewar.

        :param dewar: Dewar name (RefrigerantDewar enum)
        :type dewar: IntEnum
        """
        if self.__std_available:
            body = RequestBody(attr=self.__id + ".RefrigerantLevel()",
                               validator=float, args=dewar)
            return self.__client.call(method="exec", body=body)
        else:
            raise NotImplementedError(self.__err_msg)

    @property
    def is_dewar_filling(self) -> bool:
        """ Returns TRUE if any of the dewars is currently busy filling. """
        if self.__std_available:
            body = RequestBody(attr=self.__id + ".DewarsAreBusyFilling", validator=bool)
            return self.__client.call(method="get", body=body)
        elif self.__adv_available:
            body = RequestBody(attr=self.__id_adv + ".IsAnyDewarFilling", validator=bool)
            return self.__client.call(method="get", body=body)
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
            body = RequestBody(attr=self.__id + ".DewarsRemainingTime", validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg)

    @property
    def temp_docker(self) -> float:
        """ Returns Docker temperature in Kelvins. """
        if self.__adv_available:
            body = RequestBody(attr=self.__id_adv + ".AutoloaderCompartment.DockerTemperature",
                               validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg_adv)

    @property
    def temp_cassette(self) -> float:
        """ Returns Cassette gripper temperature in Kelvins. """
        if self.__adv_available:
            body = RequestBody(attr=self.__id_adv + ".AutoloaderCompartment.CassetteTemperature",
                               validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg_adv)

    @property
    def temp_cartridge(self) -> float:
        """ Returns Cartridge gripper temperature in Kelvins. """
        if self.__adv_available:
            body = RequestBody(attr=self.__id_adv + ".AutoloaderCompartment.CartridgeTemperature",
                               validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg_adv)

    @property
    def temp_holder(self) -> float:
        """ Returns Holder temperature in Kelvins. """
        if self.__adv_available:
            body = RequestBody(attr=self.__id_adv + ".AutoloaderCompartment.HolderTemperature",
                               validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg_adv)
