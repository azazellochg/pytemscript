from functools import lru_cache
from typing import Dict

from ..utils.misc import RequestBody
from ..utils.enums import StageAxes
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
        """ The current position of the piezo stage (x,y,z in um). """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".CurrentPosition",
                               validator=dict,
                               obj_cls=StageObj, obj_method="get")
            return self.__client.call(method="exec_special", body=body)

    @property
    def velocity(self) -> Dict:
        """ Returns a dict with current jogging velocities (x,y,z are in um/s). """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".CurrentJogVelocity",
                               validator=dict,
                               obj_cls=StageObj, obj_method="get")
            return self.__client.call(method="exec_special", body=body)

    @property
    def high_resolution(self) -> bool:
        """ """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".HighResolution",
                               validator=bool)
            return self.__client.call(method="get", body=body)

    @high_resolution.setter
    def high_resolution(self, value: bool) -> None:
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".HighResolution", value=value)
            self.__client.call(method="set", body=body)

    def go_to(self, **kwargs) -> None:
        """ Move piezo stage to the new position.
        Keyword args can be x,y,z (in um)
        """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            self.__check_limits(**kwargs)
            # convert units to meters and radians
            new_coords = dict()
            for axis in 'xyz':
                if kwargs.get(axis) is not None:
                    new_coords.update({axis: kwargs[axis] * 1e-6})

            limits = self.limits
            axes = 0
            for key, value in new_coords.items():
                if key not in 'xyz':
                    raise ValueError("Unexpected axis: %s" % key)
                if value < limits[key]['min'] or value > limits[key]['max']:
                    raise ValueError('Stage position %s=%s is out of range' % (value, key))
                axes |= getattr(StageAxes, key.upper())

            body = RequestBody(attr=self.__id, obj_cls=StageObj,
                               obj_method="set", axes=axes,
                               method="GoTo", piezo=True, **new_coords)
            self.__client.call(method="exec_special", body=body)

    def start_jogging(self, **kwargs) -> None:
        """ Start jogging with specified velocities for each axis.
        Keyword args can be x,y,z (in um/s)
        """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            self.__check_limits(**kwargs)
            # convert units to meters
            new_speed = dict()
            for axis in 'xyz':
                if kwargs.get(axis) is not None:
                    new_speed.update({axis: kwargs[axis] * 1e-6})

            axes = 0
            for key, value in new_speed.items():
                if key not in 'xyz':
                    raise ValueError("Unexpected axis: %s" % key)
                axes |= getattr(StageAxes, key.upper())

            body = RequestBody(attr=self.__id, obj_cls=StageObj,
                               obj_method="start_jog", axes=axes,
                               **new_speed)
            self.__client.call(method="exec_special", body=body)

    def stop_jogging(self, axis: StageAxes) -> None:
        """ Stop jogging for specified axis.
        :param axis: axis to stop jogging (StageAxes enum)
        :type axis: StageAxes
        """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".StopJog()", arg=axis)
            self.__client.call(method="exec", body=body)

    def reset_position(self, axis: StageAxes) -> None:
        """ Reset position for specified axis.
        :param axis: axis to reset (StageAxes enum)
        :type axis: StageAxes
        """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id + ".ResetPosition()", arg=axis)
            self.__client.call(method="exec", body=body)

    @property
    @lru_cache(maxsize=1)
    def limits(self) -> Dict:
        """ Returns a dict with piezo stage move limits. """
        if not self.__has_pstage:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id, validator=dict,
                               obj_cls=StageObj, obj_method="limits_piezo")
            return self.__client.call(method="exec_special", body=body)

    def __check_limits(self, **kwargs) -> None:
        """ Check if input axes are available. """
        available_axes = self.limits.keys()
        input_axes = kwargs.keys()
        missing_axes = set(input_axes - available_axes)
        if missing_axes:
            raise ValueError("Available piezo axes are: %s" % available_axes)
