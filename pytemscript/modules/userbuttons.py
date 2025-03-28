from typing import Dict, Callable


class EventSink:
    """ Event sink for UserButton COM object. """
    def __init__(self, name: str, func: Callable):
        self.name = name
        self.func = func

    def UserButtonEvent_Pressed(self, this):
        """ Button press event. """
        print("Button %s pressed!" % self.name)
        self.func()


class ButtonHandler:
    """ Create event handler for a specific hand panel button.

    :param button: button object
    :type button: COM object
    :param Callable func: lambda function to execute when button is pressed
    :param str assignment: new label for the button, to be displayed in TEM User Interface
    """
    def __init__(self,
                 button,
                 func: Callable,
                 assignment: str = "MyFunc"):
        self.button = button
        self.func = func
        self.sink = EventSink(self.button.Name, self.on_press)
        self.connection = None
        self.button.Assignment = assignment  # Set assignment on init

    def assign(self) -> None:
        """ Assigns the event sink to the button. """
        import comtypes.client as cc
        self.connection = cc.GetEvents(self.button, self.sink)

    def clear(self) -> None:
        """ Removes the event sink from the button. """
        if self.connection:
            self.connection.disconnect()
        self.button.Assignment = ""

    def on_press(self):
        """ Abstract method to be implemented by subclasses. """
        self.func()


class UserButtons:
    """ User buttons control. Only local client is supported. """
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
