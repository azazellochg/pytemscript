import math
import time
import logging
from ..utils.enums import StageAxes, MeasurementUnitType, StageStatus, StageHolderType


class Stage:
    """ Stage functions. """
    def __init__(self, client):
        self._client = client
        self._err_msg = "Stage is not ready"

    def _from_dict(self, **values):
        axes = 0
        position = self._client.get("tem.Stage.Position")
        for key, value in values.items():
            if key not in 'xyzab':
                raise ValueError("Unexpected axis: %s" % key)
            attr_name = key.upper()
            setattr(position, attr_name, float(value))
            axes |= getattr(StageAxes, attr_name)
        return position, axes

    def _beta_available(self):
        return self.limits['b']['unit'] != MeasurementUnitType.UNKNOWN.name

    def _change_position(self, direct=False, tries=5, **kwargs):
        attempt = 0
        while attempt < tries:
            if self._client.get("tem.Stage.Status") != StageStatus.READY:
                logging.info("Stage is not ready, retrying...")
                tries += 1
                time.sleep(1)
            else:
                # convert units to meters and radians
                new_pos = dict()
                for axis in 'xyz':
                    if axis in kwargs:
                        new_pos.update({axis: kwargs[axis] * 1e-6})
                for axis in 'ab':
                    if axis in kwargs:
                        new_pos.update({axis: math.radians(kwargs[axis])})

                speed = kwargs.get("speed", None)
                if speed is not None and not (0.0 <= speed <= 1.0):
                    raise ValueError("Speed must be within 0.0-1.0 range")

                if 'b' in new_pos and not self._beta_available():
                    raise KeyError("B-axis is not available")

                limits = self.limits
                for key, value in new_pos.items():
                    if value < limits[key]['min'] or value > limits[key]['max']:
                        raise ValueError('Stage position %s=%s is out of range' % (value, key))

                # X and Y - 1000 to + 1000(micrometers)
                # Z - 375 to 375(micrometers)
                # a - 80 to + 80(degrees)
                # b - 29.7 to + 29.7(degrees)

                new_pos, axes = self._from_dict(**new_pos)
                if not direct:
                    self._client.call("tem.Stage.MoveTo()", new_pos, axes)
                else:
                    if speed is not None:
                        self._client.call("tem.Stage.GoToWithSpeed()", new_pos, axes, speed)
                    else:
                        self._client.call("tem.Stage.GoTo()", new_pos, axes)

                break
        else:
            raise RuntimeError(self._err_msg)

    @property
    def status(self):
        """ The current state of the stage. """
        return StageStatus(self._client.get("tem.Stage.Status")).name

    @property
    def holder(self):
        """ The current specimen holder type. """
        return StageHolderType(self._client.get("tem.Stage.Holder")).name

    @property
    def position(self):
        """ The current position of the stage (x,y,z in um and a,b in degrees). """
        pos = self._client.get("tem.Stage.Position")
        result = {key.lower(): getattr(pos, key) * 1e6 for key in 'XYZ'}

        keys = 'AB' if self._beta_available() else 'A'
        result.update({key.lower(): math.degrees(getattr(pos, key)) for key in keys})

        return result

    def go_to(self, **kwargs):
        """ Makes the holder directly go to the new position by moving all axes
        simultaneously. Keyword args can be x,y,z,a or b.

        :keyword float speed: fraction of the standard speed setting (max 1.0)
        """
        self._change_position(direct=True, **kwargs)

    def move_to(self, **kwargs):
        """ Makes the holder safely move to the new position.
        Keyword args can be x,y,z,a or b.
        """
        kwargs['speed'] = None
        self._change_position(**kwargs)

    @property
    def limits(self):
        """ Returns a dict with stage move limits. """
        result = dict()
        for axis in 'xyzab':
            data = self._client.call("tem.Stage.AxisData()", StageAxes[axis.upper()])
            result[axis] = {
                'min': data.MinPos,
                'max': data.MaxPos,
                'unit': MeasurementUnitType(data.UnitType).name
            }
        return result