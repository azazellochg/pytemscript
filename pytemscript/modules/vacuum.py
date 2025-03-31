from collections import OrderedDict
from typing import Dict

from ..utils.enums import VacuumStatus, GaugeStatus, GaugePressureLevel
from ..utils.misc import RequestBody
from .extras import SpecialObj


class GaugesObj(SpecialObj):
    """ Wrapper around vacuum gauges COM object. """

    def show(self) -> Dict:
        """ Returns a dict with vacuum gauges information. """
        gauges = OrderedDict()
        for g in self.com_object:
            # g.Read()
            if g.Status == GaugeStatus.UNDEFINED:
                # set manually if undefined, otherwise fails
                pressure_level = GaugePressureLevel.UNDEFINED.name
            else:
                pressure_level = GaugePressureLevel(g.PressureLevel).name

            gauges[g.Name] = {
                "status": GaugeStatus(g.Status).name,
                "pressure": g.Pressure,
                "trip_level": pressure_level
            }

        return gauges


class Vacuum:
    """ Vacuum functions. """
    __slots__ = ("__client", "__id")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem.Vacuum"

    @property
    def status(self) -> str:
        """ Status of the vacuum system. VacuumStatus enum. """
        body = RequestBody(attr=self.__id + ".Status", validator=int)
        result = self.__client.call(method="get", body=body)

        return VacuumStatus(result).name

    @property
    def is_buffer_running(self) -> bool:
        """ Checks whether the pre-vacuum pump is currently running
        (consequences: vibrations, exposure function blocked
        or should not be called).
        """
        body = RequestBody(attr=self.__id + ".PVPRunning", validator=bool)

        return self.__client.call(method="get", body=body)

    @property
    def is_column_open(self) -> bool:
        """ The status of the column valves. """
        body = RequestBody(attr=self.__id + ".ColumnValvesOpen", validator=bool)

        return self.__client.call(method="get", body=body)

    @property
    def gauges(self) -> Dict:
        """ Returns a dict with vacuum gauges information.
        Pressure values are in Pascals.
        """
        body = RequestBody(attr=self.__id + ".Gauges", validator=dict,
                           obj_cls=GaugesObj, obj_method="show")
        result = self.__client.call(method="exec_special", body=body)

        return result

    def column_open(self) -> None:
        """ Open column valves. """
        if self.status == VacuumStatus.READY.name:
            body = RequestBody(attr=self.__id + ".ColumnValvesOpen", value=True)
            self.__client.call(method="set", body=body)
        else:
            raise RuntimeError("Vacuum status is not READY")

    def column_close(self) -> None:
        """ Close column valves. """
        body = RequestBody(attr=self.__id + ".ColumnValvesOpen", value=False)
        self.__client.call(method="set", body=body)

    def run_buffer_cycle(self) -> None:
        """ Runs a pumping cycle to empty the buffer. """
        body = RequestBody(attr=self.__id + ".RunBufferCycle()")
        self.__client.call(method="exec", body=body)
