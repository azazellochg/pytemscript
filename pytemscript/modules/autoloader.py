from functools import lru_cache

from ..utils.misc import RequestBody
from ..utils.enums import CassetteSlotStatus


class Autoloader:
    """ Sample loading functions. """
    __slots__ = ("__client", "__id", "__id_adv", "__err_msg", "__err_msg_adv")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem.AutoLoader"
        self.__id_adv = "tem_adv.AutoLoader"
        self.__err_msg = "Autoloader is not available"
        self.__err_msg_adv = "Autoloader advanced interface is not available. Requires TEM server 7.8+"

    @property
    @lru_cache(maxsize=1)
    def __adv_available(self) -> bool:
        if not self.__client.has_advanced_iface:
            return False
        else:
            body = RequestBody(attr=self.__id_adv, validator=bool)
            return self.__client.call(method="has", body=body)

    @property
    def is_available(self) -> bool:
        """ Status of the autoloader. Should be always False on Tecnai instruments. """
        body = RequestBody(attr=self.__id + ".AutoLoaderAvailable", validator=bool)

        return self.__client.call(method="get", body=body)

    @property
    def number_of_slots(self) -> int:
        """ The number of slots in a cassette. """
        if self.is_available:
            body = RequestBody(attr=self.__id + ".NumberOfCassetteSlots", validator=int)
            return self.__client.call(method="get", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    def load_cartridge(self, slot: int) -> None:
        """ Loads the cartridge in the given slot into the microscope.

        :param int slot: Slot number
        """
        if self.is_available:
            total = self.number_of_slots
            if not (0 < slot <= total):
                raise ValueError("Slot number must be between 1 and %d" % total)
            if self.slot_status(slot) != CassetteSlotStatus.OCCUPIED.name:
                raise RuntimeError("Slot %d is not occupied" % slot)

            body = RequestBody(attr=self.__id + ".LoadCartridge()", arg=slot)
            self.__client.call(method="exec", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    def unload_cartridge(self) -> None:
        """ Unloads the cartridge currently in the microscope and puts it back into its
        slot in the cassette. Does nothing if no cartridge is on stage.
        """
        if self.is_available:
            body = RequestBody(attr=self.__id + ".UnloadCartridge()")
            self.__client.call(method="exec", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    def run_inventory(self) -> None:
        """ Performs an inventory of the cassette.
        Note: This function takes considerable time to execute.
        """
        # TODO: check if cassette is present
        if self.is_available:
            body = RequestBody(attr=self.__id + ".PerformCassetteInventory()")
            self.__client.call(method="exec", body=body)
        else:
            raise RuntimeError(self.__err_msg)

    def slot_status(self, slot: int) -> str:
        """ The status of the slot specified (CassetteSlotStatus enum).

        :param int slot: Slot number
        """
        if self.is_available:
            total = self.number_of_slots
            if not (0 < slot <= total):
                raise ValueError("Slot number must be between 1 and %d" % total)

            body = RequestBody(attr=self.__id + ".SlotStatus()", arg=slot, validator=int)
            status = self.__client.call(method="exec", body=body)
            return CassetteSlotStatus(status).name
        else:
            raise RuntimeError(self.__err_msg)

    def undock_cassette(self) -> None:
        """ Moves the cassette from the docker to the capsule. """
        if self.__adv_available:
            if self.is_available:
                body = RequestBody(attr=self.__id_adv + ".UndockCassette()")
                self.__client.call(method="exec", body=body)
            else:
                raise RuntimeError(self.__err_msg)
        else:
            raise NotImplementedError(self.__err_msg_adv)

    def dock_cassette(self) -> None:
        """ Moves the cassette from the capsule to the docker. """
        if self.__adv_available:
            if self.is_available:
                body = RequestBody(attr=self.__id_adv + ".DockCassette()")
                self.__client.call(method="exec", body=body)
            else:
                raise RuntimeError(self.__err_msg)
        else:
            raise NotImplementedError(self.__err_msg_adv)

    def initialize(self) -> None:
        """ Initializes / Recovers the Autoloader for further use. """
        if self.__adv_available:
            if self.is_available:
                body = RequestBody(attr=self.__id_adv + ".Initialize()")
                self.__client.call(method="exec", body=body)
            else:
                raise RuntimeError(self.__err_msg)
        else:
            raise NotImplementedError(self.__err_msg_adv)

    def buffer_cycle(self) -> None:
        """ Synchronously runs the Autoloader buffer cycle. """
        if self.__adv_available:
            if self.is_available:
                body = RequestBody(attr=self.__id_adv + ".BufferCycle()")
                self.__client.call(method="exec", body=body)
            else:
                raise RuntimeError(self.__err_msg)
        else:
            raise NotImplementedError(self.__err_msg_adv)
