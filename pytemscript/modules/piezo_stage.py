from typing import Dict, Tuple

from .extras import StagePosition


class PiezoStage:
    """ Piezo stage functions. """
    __slots__ = ("__client", "__shortcut", "__has_pstage", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__shortcut = "tem_adv.PiezoStage"
        self.__has_pstage = None
        self.__err_msg = "PiezoStage interface is not available."

    @property
    def __adv_available(self) -> bool:
        if self.__has_pstage is None:
            self.__has_pstage = self.__client.has(self.__shortcut + ".HighResolution")
        return self.__has_pstage

    @property
    def position(self) -> Dict:
        """ The current position of the piezo stage (x,y,z in um). """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        else:
            return self.__client.call(self.__shortcut + ".CurrentPosition",
                                      obj=StagePosition, func="get")

    @property
    def position_range(self) -> Tuple[float, float]:
        """ Return min and max positions. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        else:
            return self.__client.call(self.__shortcut + ".GetPositionRange()")

    @property
    def velocity(self) -> Dict:
        """ Returns a dict with stage velocities. """
        if not self.__adv_available:
            raise NotImplementedError(self.__err_msg)
        else:
            return self.__client.call(self.__shortcut + ".CurrentJogVelocity",
                                      obj=StagePosition, func="get")
