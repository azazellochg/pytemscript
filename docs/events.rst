.. _events:

Events
======

You can receive events from user buttons when using the local client on the microscope PC.
When a button is pressed, a custom function can be executed. We provide the :class:`ButtonHandler` class
that takes care of assigning events.

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
