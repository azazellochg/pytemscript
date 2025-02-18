from ..utils.misc import RequestBody
from ..utils.enums import HatchState


class UserDoor:
    """ User door hatch controls. Requires advanced scripting. """
    __slots__ = ("__client", "__id", "__err_msg", "__tem_door",
                 "__has_control")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem_adv.UserDoorHatch"
        self.__err_msg = "Door control is unavailable"
        self.__tem_door = None
        self.__has_control = None

    @property
    def __adv_available(self) -> bool:
        if self.__tem_door is None:
            body = RequestBody(attr=self.__id, validator=bool)
            self.__tem_door = self.__client.call(method="has", body=body)
        return self.__tem_door

    @property
    def __door_available(self) -> bool:
        if self.__has_control is None:
            body = RequestBody(attr=self.__id + ".IsControlAllowed", validator=bool)
            self.__tem_door = self.__client.call(method="get", body=body)
        return self.__has_control

    @property
    def state(self) -> str:
        """ Returns door state. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)

        body = RequestBody(attr=self.__id + ".State", validator=int)
        result = self.__client.call(method="get", body=body)

        return HatchState(result).name

    def open(self) -> None:
        """ Open the door. """
        if self.__adv_available and self.__door_available:
            body = RequestBody(attr=self.__id + ".Open()")
            self.__client.call(method="exec", body=body)
        else:
            raise NotImplementedError(self.__err_msg)

    def close(self) -> None:
        """ Close the door. """
        if self.__adv_available and self.__door_available:
            body = RequestBody(attr=self.__id + ".Close()")
            self.__client.call(method="exec", body=body)
        else:
            raise NotImplementedError(self.__err_msg)
