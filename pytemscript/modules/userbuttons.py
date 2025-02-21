from typing import Dict


class UserButtons:
    """ User buttons control. Only local client is supported.

    Example usage:
    buttons = microscope.user_buttons
    buttons.show()

    import comtypes.client

    def eventHandler():
        def Pressed():
            print("L1 button was pressed!")

    buttons.L1.Assignment = "My function"
    comtypes.client.GetEvents(buttons.L1, eventHandler)

    # Simulate L1 press
    buttons.L1.Pressed()

    # Clear the assignment
    buttons.L1.Assignment = ""
    """
    __slots__ = ("_btn_cache", "_label_cache")
    valid_buttons = {"L1", "L2", "L3", "R1", "R2", "R3"}

    def __init__(self, client):
        buttons = client._scope.tem.UserButtons
        self._btn_cache = {b.Name: b for b in buttons}
        self._label_cache = {b.Name: b.Label for b in buttons}

    def show(self) -> Dict:
        """ Returns a dict with hand panel buttons labels. """
        return self._label_cache

    def __getattr__(self, name):
        if name in self.valid_buttons:
            return self._btn_cache[name]
        else:
            super().__getattribute__(name)
