from typing import Dict, Tuple

from ..utils.misc import RequestBody
from .extras import StagePosition


class PiezoStage:
    """ Piezo stage functions. """
    __slots__ = ("__client", "__id", "__has_pstage", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem_adv.PiezoStage"
        self.__has_pstage = None
        self.__err_msg = "PiezoStage interface is not available."

    @property
    def __adv_available(self) -> bool:
        if self.__has_pstage is None:
            body = RequestBody(attr=self.__id + ".HighResolution", validator=bool)
            self.__has_pstage = self.__client.call(method="has", body=body)
        return self.__has_pstage

    @property
    def position(self) -> Dict:
        """ The current position of the piezo stage (x,y,z in um). """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".CurrentPosition",
                               obj_cls=StagePosition, obj_method="get")
            return self.__client.call(method="exec_special", body=body)

    @property
    def position_range(self) -> Tuple[float, float]:
        """ Return min and max positions. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".GetPositionRange()")
            return self.__client.call(method="exec", body=body)

    @property
    def velocity(self) -> Dict:
        """ Returns a dict with stage velocities. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".CurrentJogVelocity",
                               obj_cls=StagePosition, obj_method="get")
            return self.__client.call(method="exec_special", body=body)
