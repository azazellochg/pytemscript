from .modules import *
from .utils.enums import ProductFamily, CondenserLensSystem


class Microscope:
    """ Main client interface, exposing available methods
     and properties.
    """
    __slots__ = ("__connection", "__client",
                 "acquisition", "detectors", "gun", "optics", "stem", "vacuum",
                 "autoloader", "stage", "piezo_stage", "apertures", "temperature",
                 "user_buttons", "user_door", "energy_filter", "low_dose")

    def __init__(self, connection: str = "direct", *args, **kwargs):
        self.__connection = connection
        if connection == "direct":
            from .clients.com_client import COMClient
            self.__client = COMClient(*args, **kwargs)
        elif connection == 'grpc':
            from .clients.grpc_client import GRPCClient
            self.__client = GRPCClient(*args, **kwargs)
        elif connection == 'zmq':
            from .clients.zmq_client import ZMQClient
            self.__client = ZMQClient(*args, **kwargs)
        elif connection == 'socket':
            from .clients.socket_client import SocketClient
            self.__client = SocketClient(*args, **kwargs)
        else:
            raise ValueError("Unsupported communication type")

        client = self.__client

        self.acquisition = Acquisition(client)
        self.detectors = Detectors(client)
        self.gun = Gun(client)
        self.optics = Optics(client, self.condenser_system)
        self.stem = Stem(client)
        self.vacuum = Vacuum(client)
        self.autoloader = Autoloader(client)
        self.stage = Stage(client)
        self.piezo_stage = PiezoStage(client)
        self.apertures = Apertures(client)
        self.temperature = Temperature(client)
        self.user_buttons = UserButtons(client)

        if client.has_advanced_iface:
            self.user_door = UserDoor(client)
            self.energy_filter = EnergyFilter(client)

        if kwargs.get("useLD", False):
            self.low_dose = LowDose(client)

    @property
    def family(self) -> str:
        """ Returns the microscope product family / platform. """
        value = self.__client.get_from_cache("tem.Configuration.ProductFamily")
        return ProductFamily(value).name

    @property
    def condenser_system(self) -> str:
        """ Returns the type of condenser lens system: two or three lenses. """
        value = self.__client.get_from_cache("tem.Configuration.CondenserLensSystem")
        return CondenserLensSystem(value).name

    def disconnect(self) -> None:
        """ Disconnects the remote client. """
        if self.__connection != "direct":
            self.__client.disconnect()
