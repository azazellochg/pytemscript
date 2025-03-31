Events
======

You can receive events from multifunction buttons (L1, L2, L3, R1, R2, R3) on the hand panels when using the local client on the microscope PC.
Each button can be assigned with a custom Python function that will be executed upon pressing.
We provide the :meth:`~pytemscript.modules.ButtonHandler` class that takes care of assigning events.

.. note:: Don't forget to clear the custom button assignment at the end using `clear()` method. This will restore the previous assignment.

See example below:

.. code-block:: python

    import comtypes.client as cc
    from pytemscript.modules import ButtonHandler

    buttons = microscope.user_buttons
    buttons.show()

    def my_function(x, y):
        print(x+y)

    event_handler = ButtonHandler(buttons.L1, lambda: my_function(2, 3), "MyFuncName")
    event_handler.assign()
    cc.PumpEvents(10) # wait 10s for events (blocking)
    # Now press L1, it should print the result: 5
    event_handler.clear()


.. autoclass:: pytemscript.modules.ButtonHandler
    :members: assign, clear
