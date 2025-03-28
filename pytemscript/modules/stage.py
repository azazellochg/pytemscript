from functools import lru_cache
from typing import Dict, Optional
import math
import time
import logging

from ..utils.misc import RequestBody
from ..utils.enums import MeasurementUnitType, StageStatus, StageHolderType, StageAxes
from .extras import StageObj


class Stage:
    """ Stage functions. """
    __slots__ = ("__client", "__id", "__err_msg")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem.Stage"
        self.__err_msg = "Timeout. Stage is not ready"

    @property
    def _beta_available(self) -> bool:
        return self.limits['b']['unit'] != MeasurementUnitType.UNKNOWN.name

    def _wait_for_stage(self, tries: int = 10) -> None:
        """ Wait for stage to become ready. """
        attempt = 0
        while attempt < tries:
            body = RequestBody(attr=self.__id + ".Status", validator=int)
            if self.__client.call(method="get", body=body) != StageStatus.READY:
                logging.info("Stage is not ready, waiting..")
                tries += 1
                time.sleep(1)
            else:
                break
        else:
            raise RuntimeError(self.__err_msg)

    def _change_position(self,
                         direct: bool = False,
                         relative: bool = False,
                         speed: Optional[float] = None,
                         **kwargs) -> None:
        """
        Execute stage move to a new position.

        :param bool direct: use Goto instead of MoveTo
        :param bool relative: use relative coordinates
        :param float speed: Goto speed
        :param kwargs: new coordinates
        """
        self._wait_for_stage(tries=5)

        if relative:
            current_pos = self.position
            for axis in kwargs:
                kwargs[axis] += current_pos[axis]

        # convert units to meters and radians
        new_coords = dict()
        for axis in 'xyz':
            if kwargs.get(axis) is not None:

                new_coords.update({axis: kwargs[axis] * 1e-6})
        for axis in 'ab':
            if kwargs.get(axis) is not None:
                new_coords.update({axis: math.radians(kwargs[axis])})

        if speed is not None and not (0.0 <= speed <= 1.0):
            raise ValueError("Speed must be within 0.0-1.0 range")

        if 'b' in new_coords and not self._beta_available:
            raise KeyError("B-axis is not available")

        limits = self.limits
        axes = 0
        for key, value in new_coords.items():
            if key not in 'xyzab':
                raise ValueError("Unexpected axis: %s" % key)
            if value < limits[key]['min'] or value > limits[key]['max']:
                raise ValueError('Stage position %s=%s is out of range' % (value, key))
            axes |= getattr(StageAxes, key.upper())

        # X and Y - 1000 to + 1000(micrometers)
        # Z - 375 to 375(micrometers)
        # a - 80 to + 80(degrees)
        # b - 29.7 to + 29.7(degrees)

        if not direct:
            body = RequestBody(attr=self.__id, obj_cls=StageObj,
                               obj_method="set", axes=axes,
                               method="MoveTo", **new_coords)
            self.__client.call(method="exec_special", body=body)
        else:
            if speed is not None:
                body = RequestBody(attr=self.__id, obj_cls=StageObj,
                                   obj_method="set", axes=axes, speed=speed,
                                   method="GoToWithSpeed", **new_coords)
                self.__client.call(method="exec_special", body=body)
            else:
                body = RequestBody(attr=self.__id, obj_cls=StageObj,
                                   obj_method="set", axes=axes,
                                   method="GoTo", **new_coords)
                self.__client.call(method="exec_special", body=body)

        self._wait_for_stage(tries=10)

    @property
    def status(self) -> str:
        """ The current state of the stage. StageStatus enum. """
        body = RequestBody(attr=self.__id + ".Status", validator=int)
        result = self.__client.call(method="get", body=body)

        return StageStatus(result).name

    @property
    def holder(self) -> str:
        """ The current specimen holder type. StageHolderType enum. """
        body = RequestBody(attr=self.__id + ".Holder", validator=int)
        result = self.__client.call(method="get", body=body)

        return StageHolderType(result).name

    @property
    def position(self) -> Dict:
        """ The current position of the stage (x,y,z in um and a,b in degrees). """
        body = RequestBody(attr=self.__id + ".Position", validator=dict,
                           obj_cls=StageObj, obj_method="get",
                           a=True, b=self._beta_available)

        return self.__client.call(method="exec_special", body=body)

    def go_to(self,
              relative: bool = False,
              speed: Optional[float] = None,
              **kwargs) -> None:
        """ Makes the holder directly go to the new position by moving all axes
        simultaneously. Keyword args can be x,y,z,a or b.
        (x,y,z in um and a,b in degrees)

        :param bool relative: Use relative move instead of absolute position.
        :param float speed: fraction of the standard speed setting (max 1.0)
        """
        self._change_position(direct=True, relative=relative, speed=speed, **kwargs)

    def move_to(self, relative: bool = False, **kwargs) -> None:
        """ Makes the holder safely move to the new position.
        Keyword args can be x,y,z,a or b (x,y,z in um and a,b in degrees).

        :param bool relative: Use relative move instead of absolute position.
        """
        self._change_position(relative=relative, **kwargs)

    @property
    @lru_cache(maxsize=1)
    def limits(self) -> Dict:
        """ Returns a dict with stage move limits. """
        body = RequestBody(attr=self.__id, validator=dict,
                           obj_cls=StageObj, obj_method="limits")
        return self.__client.call(method="exec_special", body=body)
