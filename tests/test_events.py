import comtypes.client as cc

from pytemscript.microscope import Microscope
from pytemscript.utils.enums import ScreenPosition
from pytemscript.modules import ButtonHandler


def main() -> None:
    """ Testing acquisition functions. """

    microscope = Microscope()
    acquisition = microscope.acquisition
    buttons = microscope.user_buttons
    print("User buttons:", buttons.show())

    def screen_toggle():
        current_pos = acquisition.screen
        if current_pos == ScreenPosition.UP:
            new_pos = ScreenPosition.DOWN
        elif current_pos == ScreenPosition.DOWN:
            new_pos = ScreenPosition.UP
        else:
            raise RuntimeError(f"Unknown screen position: {current_pos}")

        print("Toggling screen lift..")
        acquisition.screen = new_pos
        print("OK\nNew screen position:", acquisition.screen)

    event_handler = ButtonHandler(buttons.L1,
                                  lambda: screen_toggle(),
                                  "MyScreenLift")
    event_handler.assign()
    print("Please press L1 button within 10 seconds. It will toggle the screen lift.")
    cc.PumpEvents(10)  # wait 10s for events (blocking)
    event_handler.clear()


if __name__ == '__main__':
    main()
