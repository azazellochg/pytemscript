Components
==========

This section covers the main components of Pytemscript.

The COM interface
-----------------

As a user, you don't have to deal with the COM objects directly. Below we provide a list of objects exposed
by the scripting interfaces and implemented in ``pytemscript`` API.
The scripting manual of your microscope (``scripting.pdf``) can be located in the ``C:\Titan\Tem_help\manual`` or
``C:\Tecnai\tem_help\manual`` directory. Advanced scripting manual can be found in
``C:\Titan\Scripting\Advanced TEM Scripting User Guide.pdf``.

Relative to TEM V1.9 standard scripting adapter:

    * Acquisition
    * ApertureMechanismCollection (untested)
    * AutoLoader
    * BlankerShutter
    * Camera
    * Configuration
    * Gun
    * Gun1
    * Illumination
    * InstrumentModeControl
    * Projection
    * Stage
    * TemperatureControl
    * UserButtons (with event handling)
    * Vacuum

Relative to TEM V1.2 advanced scripting adapter:

    * Acquisitions
    * Autoloader
    * EnergyFilter
    * Phaseplate
    * PiezoStage (untested)
    * Source
    * TemperatureControl
    * UserDoorHatch (untested)

Microscope class
----------------

The `microscope <microscope.html>`_ class provides the main interface to the microscope. It is used to connect to the instrument locally or over the network.

Events
------

You can receive events from hand panel buttons when using the local client on the microscope PC. See `events <events.html>`_ page for details.

Enumerations
------------

Many of the attributes set and return values from enumerations. This minimizes typos when dealing with integer or string static values.
The complete list can be found on the `enumerations <enumerations.html>`_ page.

Images
------

Two main acquisition methods :meth:`~pytemscript.modules.Acquisition.acquire_tem_image` and
:meth:`~pytemscript.modules.Acquisition.acquire_stem_image` return an :meth:`~pytemscript.modules.Image` object
that has the following methods and properties:

.. autoclass:: pytemscript.modules.Image
    :members: save

Vectors
-------

Some attributes handle two dimensional vectors that have X and Y values (e.g. image shift or gun tilt). These
attributes accept and return a :meth:`~pytemscript.modules.Vector` of two floats. Vectors can be multiplied, subtracted etc. as shown below.
You can also use a list or a tuple to set vector attributes.

.. code-block:: python

    from pytemscript.modules import Vector
    shift = Vector(0.5,-0.5)
    shift += (0.4, 0.2)
    shift *= 2
    microscope.optics.illumination.beam_shift = shift
    projection.image_shift = (0.05, 0.1)
    projection.image_shift = [0.05, 0.1]

.. autoclass:: pytemscript.modules.Vector
    :members: set_limits, check_limits, get, set
