from typing import Dict

from ..utils.enums import VacuumStatus, GaugeStatus, GaugePressureLevel
from .extras import SpecialObj


class GaugesObj(SpecialObj):
    """ Wrapper around vacuum gauges COM object. """

    def show(self) -> Dict:
        """ Returns a dict with vacuum gauges information. """
        gauges = {}
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
    __slots__ = ("__client", "__shortcut")

    def __init__(self, client):
        self.__client = client
        self.__shortcut = "tem.Vacuum"

    @property
    def status(self) -> str:
        """ Status of the vacuum system. """
        return VacuumStatus(self.__client.get(self.__shortcut + ".Status")).name

    @property
    def is_buffer_running(self) -> bool:
        """ Checks whether the prevacuum pump is currently running
        (consequences: vibrations, exposure function blocked
        or should not be called).
        """
        return bool(self.__client.get(self.__shortcut + ".PVPRunning"))

    @property
    def is_column_open(self) -> bool:
        """ The status of the column valves. """
        return bool(self.__client.get(self.__shortcut + ".ColumnValvesOpen"))

    @property
    def gauges(self) -> Dict:
        """ Returns a dict with vacuum gauges information.
        Pressure values are in Pascals.
        """
        return self.__client.call(self.__shortcut + ".Gauges",
                                  obj=GaugesObj, func="show")

    def column_open(self) -> None:
        """ Open column valves. """
        self.__client.set(self.__shortcut + ".ColumnValvesOpen", True)

    def column_close(self) -> None:
        """ Close column valves. """
        self.__client.set(self.__shortcut + ".ColumnValvesOpen", False)

    def run_buffer_cycle(self) -> None:
        """ Runs a pumping cycle to empty the buffer. """
        self.__client.call(self.__shortcut + ".RunBufferCycle()")
