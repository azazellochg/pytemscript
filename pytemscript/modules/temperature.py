from functools import lru_cache

from ..utils.enums import RefrigerantDewar
from ..utils.misc import RequestBody


class Temperature:
    """ LN dewars and temperature controls. """
    __slots__ = ("__client", "__id", "__id_adv", "__err_msg", "__err_msg_adv")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem.TemperatureControl"
        self.__id_adv = "tem_adv.TemperatureControl"
        self.__err_msg = "TemperatureControl is not available"
        self.__err_msg_adv = "TemperatureControl advanced interface is not available. Requires TEM server 7.8+"
    
    @property
    @lru_cache(maxsize=1)
    def __has_tmpctrl(self) -> bool:
        body = RequestBody(attr=self.__id, validator=bool)

        return self.__client.call(method="has", body=body)

    @property
    @lru_cache(maxsize=1)
    def __has_tmpctrl_adv(self) -> bool:
        body = RequestBody(attr=self.__id_adv, validator=bool)

        return self.__client.call(method="has", body=body)

    @property
    def is_available(self) -> bool:
        """ Status of the temperature control. Should be always False on Tecnai instruments. """
        if self.__has_tmpctrl:
            body = RequestBody(attr=self.__id + ".TemperatureControlAvailable", validator=bool)
            return self.__client.call(method="has", body=body)
        else:
            return False

    def force_refill(self) -> None:
        """ Forces LN refill if the level is below 70%, otherwise returns an error.
        Note: this function takes considerable time to execute.
        """
        if self.__has_tmpctrl:
            body = RequestBody(attr=self.__id + ".ForceRefill()")
        elif self.__has_tmpctrl_adv:
            body = RequestBody(attr=self.__id_adv + ".RefillAllDewars()")
        else:
            raise NotImplementedError(self.__err_msg)

        self.__client.call(method="exec", body=body)

    def dewar_level(self, dewar: RefrigerantDewar) -> float:
        """ Returns the LN level (%) in a dewar.

        :param RefrigerantDewar dewar: Dewar name
        """
        if self.__has_tmpctrl:
            body = RequestBody(attr=self.__id + ".RefrigerantLevel()",
                               validator=float, arg=dewar)
            return self.__client.call(method="exec", body=body)
        else:
            raise NotImplementedError(self.__err_msg)

    @property
    def is_dewar_filling(self) -> bool:
        """ Returns TRUE if any of the dewars is currently busy filling. """
        if self.__has_tmpctrl:
            body = RequestBody(attr=self.__id + ".DewarsAreBusyFilling", validator=bool)
        elif self.__has_tmpctrl_adv:
            body = RequestBody(attr=self.__id_adv + ".IsAnyDewarFilling", validator=bool)
        else:
            raise NotImplementedError(self.__err_msg)

        return self.__client.call(method="get", body=body)

    @property
    def dewars_time(self) -> int:
        """ Returns remaining time (seconds) until the next dewar refill.
        Returns -1 if no refill is scheduled (e.g. All room temperature, or no
        dewar present).
        """
        # TODO: check if returns -60 at room temperature
        if self.__has_tmpctrl:
            body = RequestBody(attr=self.__id + ".DewarsRemainingTime", validator=int)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg)

    @property
    def temp_docker(self) -> float:
        """ Returns Docker temperature in Kelvins. """
        if self.__has_tmpctrl_adv:
            body = RequestBody(attr=self.__id_adv + ".AutoloaderCompartment.DockerTemperature",
                               validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg_adv)

    @property
    def temp_cassette(self) -> float:
        """ Returns Cassette gripper temperature in Kelvins. """
        if self.__has_tmpctrl_adv:
            body = RequestBody(attr=self.__id_adv + ".AutoloaderCompartment.CassetteTemperature",
                               validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg_adv)

    @property
    def temp_cartridge(self) -> float:
        """ Returns Cartridge gripper temperature in Kelvins. """
        if self.__has_tmpctrl_adv:
            body = RequestBody(attr=self.__id_adv + ".AutoloaderCompartment.CartridgeTemperature",
                               validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg_adv)

    @property
    def temp_holder(self) -> float:
        """ Returns Holder temperature in Kelvins. """
        if self.__has_tmpctrl_adv:
            body = RequestBody(attr=self.__id_adv + ".ColumnCompartment.HolderTemperature",
                               validator=float)
            return self.__client.call(method="get", body=body)
        else:
            raise NotImplementedError(self.__err_msg_adv)
