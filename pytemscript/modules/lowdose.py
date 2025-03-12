from ..utils.misc import RequestBody
from ..utils.enums import LDState, LDStatus


class LowDose:
    """ Low Dose functions. """
    __slots__ = ("__client", "__id", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem_lowdose"
        self.__err_msg = "Low Dose is not available or not active"

    @property
    def is_available(self) -> bool:
        """ Return True if Low Dose is available. """
        avail = RequestBody(attr=self.__id + ".LowDoseAvailable", validator=bool)
        init = RequestBody(attr=self.__id + ".IsInitialized", validator=bool)

        return (self.__client.has_lowdose_iface and
                self.__client.call(method="get", body=avail) and
                self.__client.call(method="get", body=init))

    @property
    def is_active(self) -> bool:
        """ Check if the Low Dose is ON. """
        if self.is_available:
            body = RequestBody(attr=self.__id + ".LowDoseActive", validator=int)
            result = self.__client.call(method="get", body=body)
            return LDStatus(result) == LDStatus.IS_ON
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def state(self) -> str:
        """ Low Dose state (LDState enum). (read/write) """
        if self.is_available and self.is_active:
            body = RequestBody(attr=self.__id + ".LowDoseState", validator=int)
            result = self.__client.call(method="get", body=body)
            return LDState(result).name
        else:
            raise RuntimeError(self.__err_msg)

    @state.setter
    def state(self, state: LDState) -> None:
        if self.is_available:
            body = RequestBody(attr=self.__id + ".LowDoseState", value=state)
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    def on(self) -> None:
        """ Switch ON Low Dose."""
        if self.is_available:
            body = RequestBody(attr=self.__id + ".LowDoseActive", value=LDStatus.IS_ON)
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    def off(self) -> None:
        """ Switch OFF Low Dose."""
        if self.is_available:
            body = RequestBody(attr=self.__id + ".LowDoseActive", value=LDStatus.IS_OFF)
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError(self.__err_msg)
