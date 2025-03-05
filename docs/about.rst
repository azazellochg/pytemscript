About
=====

The COM interface
-----------------

The methods and classes represent the COM objects exposed by the *Scripting* interface.
The interface is described in detail in the scripting manual of your microscope
(usually in the file ``scripting.pdf`` located in the ``C:\Titan\Tem_help\manual`` or
``C:\Tecnai\tem_help\manual`` directories). Advanced scripting manual can be found in
``C:\Titan\Scripting\Advanced TEM Scripting User Guide.pdf``.

The manual is your ultimate reference, this documentation will only describe the
Python wrapper to the COM interface.

Microscope class
----------------

The :ref:`microscope` class provides the main interface to the microscope. It can be used to connect and operate the instrument directly or over the network.

Events
------

You can receive events from user buttons when using the local client on the microscope PC. See :ref:`events` page for details.

Enumerations
------------

Many of the attributes set and return values from enumerations. The complete list can be found on the :ref:`enumerations` page.

Images
------

Two main acquisition functions: :meth:`~pytemscript.modules.Acquisition.acquire_tem_image` and
:meth:`~pytemscript.modules.Acquisition.acquire_stem_image` return an :class:`Image` object
that has the following methods and properties:

.. autoclass:: pytemscript.modules.Image
    :members: save

Vectors
-------

Some attributes handle two dimensional vectors that have X and Y values (e.g. image shift or gun tilt). These
attributes accept and return a :class:`Vector` of two floats. Vectors can be multiplied, subtracted etc.:

.. code-block:: python

    from pytemscript.modules import Vector
    shift = Vector(0.5,-0.5)
    shift += (0.4, 0.2)
    shift *= 2
    microscope.optics.illumination.beam_shift = shift

.. autoclass:: pytemscript.modules.Vector
    :members: set_limits, check_limits, get, set
