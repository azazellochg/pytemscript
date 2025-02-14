from ..utils.enums import HatchState


class UserDoor:
    """ User door hatch controls. Requires advanced scripting. """
    __slots__ = ("__client", "__shortcut", "__err_msg", "__tem_door")

    def __init__(self, client):
        self.__client = client
        self.__shortcut = "tem_adv.UserDoorHatch"
        self.__err_msg = "Door control is unavailable"
        self.__tem_door = None

    @property
    def __adv_available(self) -> bool:
        if self.__tem_door is None:
            self.__tem_door = self.__client.has(self.__shortcut)
        return self.__tem_door

    @property
    def state(self) -> str:
        """ Returns door state. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        return HatchState(self.__client.get(self.__shortcut + ".State")).name

    def open(self) -> None:
        """ Open the door. """
        if self.__adv_available and self.__client.get(self.__shortcut + ".IsControlAllowed"):
            self.__client.call(self.__shortcut + ".Open()")
        else:
            raise NotImplementedError(self.__err_msg)

    def close(self) -> None:
        """ Close the door. """
        if self.__adv_available and self.__client.get(self.__shortcut + ".IsControlAllowed"):
            self.__client.call(self.__shortcut + ".Close()")
        else:
            raise NotImplementedError(self.__err_msg)
