from ..utils.enums import LDState, LDStatus


class LowDose:
    """ Low Dose functions. """
    __slots__ = ("__client", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__err_msg = "Low Dose is not available"

    @property
    def is_available(self) -> bool:
        """ Return True if Low Dose is available. """
        return (self.__client.has_lowdose_iface and
                self.__client.get("tem_lowdose.LowDoseAvailable") and
                self.__client.get("tem_lowdose.IsInitialized"))

    @property
    def is_active(self) -> bool:
        """ Check if the Low Dose is ON. """
        if self.is_available:
            return LDStatus(self.__client.get("tem_lowdose.LowDoseActive")) == LDStatus.IS_ON
        else:
            raise RuntimeError(self.__err_msg)

    @property
    def state(self) -> str:
        """ Low Dose state (LDState enum). (read/write) """
        if self.is_available and self.is_active:
            return LDState(self.__client.get("tem_lowdose.LowDoseState")).name
        else:
            raise RuntimeError(self.__err_msg)

    @state.setter
    def state(self, state: LDState) -> None:
        if self.is_available:
            self.__client.set("tem_lowdose.LowDoseState", state)
        else:
            raise RuntimeError(self.__err_msg)

    def on(self) -> None:
        """ Switch ON Low Dose."""
        if self.is_available:
            self.__client.set("tem_lowdose.LowDoseActive", LDStatus.IS_ON)
        else:
            raise RuntimeError(self.__err_msg)

    def off(self) -> None:
        """ Switch OFF Low Dose."""
        if self.is_available:
            self.__client.set("tem_lowdose.LowDoseActive", LDStatus.IS_OFF)
        else:
            raise RuntimeError(self.__err_msg)
