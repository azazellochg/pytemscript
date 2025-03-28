from functools import lru_cache

from .modules import *
from .utils.misc import RequestBody
from .utils.enums import ProductFamily, CondenserLensSystem


class Microscope:
    """ Main client interface exposing available methods and properties.

    :param str connection: Client connection: direct, socket or utapi. Defaults to direct.
    :keyword str host: Remote hostname or IP address
    :keyword int port: Remote port number
    :keyword bool useLD: Connect to LowDose server on microscope PC (limited control only)
    :keyword bool useTecnaiCCD: Connect to TecnaiCCD plugin on microscope PC that controls Digital Micrograph (maybe faster than via TIA / std scripting)
    :keyword bool debug: Debug mode

    Usage:
            >>> microscope = Microscope()
            >>> curr_pos = microscope.stage.position
            >>> print(curr_pos['Y'])
            >>> 24.05
            >>> microscope.stage.move_to(x=-30, y=25.5)

            >>> beam_shift = microscope.optics.illumination.beam_shift
            >>> defocus = microscope.optics.projection.defocus
            >>> microscope.optics.normalize_all()

    """
    __slots__ = ("__connection", "__client",
                 "acquisition", "gun", "optics", "stem", "vacuum",
                 "autoloader", "stage", "piezo_stage", "apertures", "temperature",
                 "user_buttons", "user_door", "energy_filter", "low_dose")

    def __init__(self, connection: str = "direct", *args, **kwargs) -> None:
        self.__connection = connection
        if connection == "direct":
            from .clients.com_client import COMClient
            self.__client = COMClient(*args, **kwargs)
        elif connection == 'utapi':
            from .clients.utapi_client import UTAPIClient
            self.__client = UTAPIClient(*args, **kwargs)
        elif connection == 'socket':
            from .clients.socket_client import SocketClient
            self.__client = SocketClient(*args, **kwargs)
        else:
            raise ValueError("Unsupported communication type")

        client = self.__client

        self.acquisition = Acquisition(client)
        self.gun = Gun(client)
        self.optics = Optics(client, self.condenser_system)
        self.stem = Stem(client)
        self.vacuum = Vacuum(client)
        self.autoloader = Autoloader(client)
        self.stage = Stage(client)
        self.apertures = Apertures(client)
        self.temperature = Temperature(client)

        if connection == "direct":
            self.user_buttons = UserButtons(client)

        if client.has_advanced_iface:
            self.piezo_stage = PiezoStage(client)
            self.user_door = UserDoor(client)
            self.energy_filter = EnergyFilter(client)

        if kwargs.get("useLD", False) and client.has_lowdose_iface:
            self.low_dose = LowDose(client)

    @property
    @lru_cache(maxsize=1)
    def family(self) -> str:
        """ Returns the microscope product family / platform (ProductFamily enum). """
        body = RequestBody(attr="tem.Configuration.ProductFamily", validator=int)
        result = self.__client.call(method="get", body=body)

        return ProductFamily(result).name

    @property
    @lru_cache(maxsize=1)
    def condenser_system(self) -> str:
        """ Returns the type of condenser lens system: two or three lenses (CondenserLensSystem enum). """
        body = RequestBody(attr="tem.Configuration.CondenserLensSystem", validator=int)
        result = self.__client.call(method="get", body=body)

        return CondenserLensSystem(result).name

    def disconnect(self) -> None:
        """ Disconnects the client. """
        self.__client.disconnect()
