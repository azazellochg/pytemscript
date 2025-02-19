from typing import Dict

from ..utils.misc import RequestBody
from .extras import SpecialObj


class ButtonsObj(SpecialObj):
    """ Wrapper around buttons COM object. """

    def show(self) -> Dict:
        """ Returns a dict with buttons assignment. """
        buttons = {}
        for b in self.com_object:
            buttons[b.Name] = b.Label

        return buttons


class UserButtons:
    """ User buttons control. """
    __slots__ = ("__client",)
    valid_buttons = ["L1", "L2", "L3", "R1", "R2", "R3"]

    def __init__(self, client):
        self.__client = client

    def show(self) -> Dict:
        """ Returns a dict with assigned hand panels buttons. """
        body = RequestBody(attr="tem.UserButtons", validator=dict,
                           obj_cls=ButtonsObj, obj_method="show")
        result = self.__client.call(method="exec_special", body=body)

        return result

    def __getattr__(self, name):
        if name in self.valid_buttons:
            getattr(self.__client, name)

    def __setattr__(self, name, value):
        if name in self.valid_buttons:
            setattr(self.__client, name, value)
        else:
            super().__setattr__(name, value)
