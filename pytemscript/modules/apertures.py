from typing import Dict
from collections import OrderedDict
from functools import lru_cache

from .extras import SpecialObj
from ..utils.misc import RequestBody
from ..utils.enums import MechanismId, MechanismState, ApertureType


class AperturesObj(SpecialObj):
    """ Wrapper around apertures COM object. """

    def show(self) -> Dict:
        """ Returns a dict with apertures information. """
        apertures = OrderedDict()
        for ap in self.com_object:
            apertures[MechanismId(ap.Id).name] = {
                "retractable": ap.IsRetractable,
                "state": MechanismState(ap.State).name,
                "sizes": [int(a.Diameter) for a in ap.ApertureCollection],
                "types": [ApertureType(a.Type).name for a in ap.ApertureCollection],
            }

        return apertures

    def _find_aperture(self, name: MechanismId):
        """ Helper method to find the aperture object by name. """
        for ap in self.com_object:
            if name == MechanismId(ap.Id):
                return ap
        raise KeyError("No aperture with name %s" % name.name)

    def enable(self, name: MechanismId) -> None:
        ap = self._find_aperture(name)
        ap.Enable()

    def disable(self, name: MechanismId) -> None:
        ap = self._find_aperture(name)
        ap.Disable()

    def retract(self, name: MechanismId) -> None:
        ap = self._find_aperture(name)
        if ap.IsRetractable:
            ap.Retract()
        else:
            raise NotImplementedError("Aperture %s is not retractable" % name.name)

    def select(self, name: MechanismId, size: int) -> None:
        ap = self._find_aperture(name)
        if ap.State == MechanismState.DISABLED:
            ap.Enable()
        for a in ap.ApertureCollection:
            if int(a.Diameter) == size:
                ap.SelectAperture(a)
                if int(ap.SelectedAperture.Diameter) == size:
                    return
                else:
                    raise RuntimeError("Could not select aperture %s=%d" % (name.name, size))


class Apertures:
    """ Apertures and VPP controls. """
    __slots__ = ("__client", "__id", "__id_adv",
                 "__err_msg", "__err_msg_vpp")

    def __init__(self, client):
        self.__client = client
        self.__id = "tem.ApertureMechanismCollection"
        self.__id_adv = "tem_adv.PhasePlate"
        self.__err_msg = "Apertures interface is not available. Requires a separate license"
        self.__err_msg_vpp = "Either no VPP found or it's not enabled and inserted"

    @property
    @lru_cache(maxsize=1)
    def __std_available(self) -> bool:
        body = RequestBody(attr=self.__id, validator=bool)

        return self.__client.call(method="has", body=body)

    @property
    def vpp_position(self) -> int:
        """ Returns the index of the current VPP preset position. """
        if not self.__client.has_advanced_iface:
            raise RuntimeError("No advanced scripting available")
        try:
            body = RequestBody(attr=self.__id_adv + ".GetCurrentPresetPosition", validator=int)
            return self.__client.call(method="get", body=body) + 1
        except:
            raise RuntimeError(self.__err_msg_vpp)

    def vpp_next_position(self) -> None:
        """ Goes to the next preset location on the VPP aperture. """
        if not self.__client.has_advanced_iface:
            raise RuntimeError("No advanced scripting available")
        try:
            body = RequestBody(attr=self.__id_adv + ".SelectNextPresetPosition()")
            self.__client.call(method="exec", body=body)
        except:
            raise RuntimeError(self.__err_msg_vpp)

    def enable(self, aperture: MechanismId) -> None:
        """ Enable a specific aperture.

        :param MechanismId aperture: Aperture name
        """
        if not self.__std_available:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id, obj_cls=AperturesObj,
                               obj_method="enable", name=aperture)
            self.__client.call(method="exec_special", body=body)

    def disable(self, aperture: MechanismId) -> None:
        """ Disable a specific aperture.

        :param MechanismId aperture: Aperture name
        """
        if not self.__std_available:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id, obj_cls=AperturesObj,
                               obj_method="disable", name=aperture)
            self.__client.call(method="exec_special", body=body)

    def retract(self, aperture: MechanismId) -> None:
        """ Retract a specific aperture.

        :param MechanismId aperture: Aperture name
        """
        if not self.__std_available:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id, obj_cls=AperturesObj,
                               obj_method="retract", name=aperture)
            self.__client.call(method="exec_special", body=body)

    def select(self, aperture: MechanismId, size: int) -> None:
        """ Select a specific aperture.

        :param MechanismId aperture: Aperture name
        :param int size: Aperture size
        """
        if not self.__std_available:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id, obj_cls=AperturesObj,
                               obj_method="select", name=aperture, size=size)
            self.__client.call(method="exec_special", body=body)

    def show(self) -> Dict:
        """ Returns a dict with apertures information. """
        if not self.__std_available:
            raise NotImplementedError(self.__err_msg)
        else:
            body = RequestBody(attr=self.__id,
                               validator=dict,
                               obj_cls=AperturesObj,
                               obj_method="show")
            return self.__client.call(method="exec_special", body=body)
