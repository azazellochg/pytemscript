from functools import lru_cache
from typing import Dict, Tuple

from ..utils.misc import RequestBody
from .extras import StageObj


class PiezoStage:
    """ Piezo stage functions. """
    __slots__ = ("__client", "__id", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem_adv.PiezoStage"
        self.__err_msg = "PiezoStage interface is not available."

    @property
    @lru_cache(maxsize=1)
    def __has_pstage(self) -> bool:
        body = RequestBody(attr=self.__id + ".HighResolution", validator=bool)

        return self.__client.call(method="has", body=body)

    @property
    def position(self) -> Dict:
        """ The current position of the piezo stage (x,y,z in um and a,b in degrees). """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".CurrentPosition",
                               validator=dict,
                               obj_cls=StageObj, obj_method="get", a=True)
            return self.__client.call(method="exec_special", body=body)

    @property
    def position_range(self) -> Tuple[float, float]:
        """ Return min and max positions. """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".GetPositionRange()")
            return self.__client.call(method="exec", body=body)

    @property
    def velocity(self) -> Dict:
        """ Returns a dict with stage velocities (x,y,z are in um/s and a,b in deg/s). """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".CurrentJogVelocity",
                               validator=dict,
                               obj_cls=StageObj, obj_method="get",
                               get_speed=True)
            return self.__client.call(method="exec_special", body=body)
