from functools import lru_cache

from ..utils.misc import RequestBody
from ..utils.enums import HatchState


class UserDoor:
    """ User door hatch controls. Requires advanced scripting. """
    __slots__ = ("__client", "__id", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem_adv.UserDoorHatch"
        self.__err_msg = "Door control is unavailable"

    @property
    @lru_cache(maxsize=1)
    def __has_door(self) -> bool:
        body = RequestBody(attr=self.__id, validator=bool)

        return self.__client.call(method="has", body=body)

    @property
    @lru_cache(maxsize=1)
    def __door_available(self) -> bool:
        body = RequestBody(attr=self.__id + ".IsControlAllowed", validator=bool)

        return self.__client.call(method="get", body=body)

    @property
    def state(self) -> str:
        """ Returns door state (HatchState enum). """
        if not self.__has_door:
            raise NotImplementedError(self.__err_msg)

        body = RequestBody(attr=self.__id + ".State", validator=int)
        result = self.__client.call(method="get", body=body)

        return HatchState(result).name

    def open(self) -> None:
        """ Open the door. """
        if self.__has_door and self.__door_available:
            body = RequestBody(attr=self.__id + ".Open()")
            self.__client.call(method="exec", body=body)
        else:
            raise NotImplementedError(self.__err_msg)

    def close(self) -> None:
        """ Close the door. """
        if self.__has_door and self.__door_available:
            body = RequestBody(attr=self.__id + ".Close()")
            self.__client.call(method="exec", body=body)
        else:
            raise NotImplementedError(self.__err_msg)
