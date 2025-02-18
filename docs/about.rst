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

The :ref:`microscope` class provides the main interface to the microscope.

Enumerations
------------

Many of the attributes return values from enumerations. The complete list can be found in the :ref:`enumerations` section.

Images
------

Two acquisition functions: :meth:`~pytemscript.modules.Acquisition.acquire_tem_image` and
:meth:`~pytemscript.modules.Acquisition.acquire_stem_image` return an :class:`Image` object
that has the following methods and properties:

.. autoclass:: pytemscript.modules.Image
    :members: width, height, bit_depth, pixel_type, data, save, name, metadata

Vectors
-------

Some attributes handle two dimensional vectors that have X and Y values (e.g. image shift or gun tilt). These
attributes return a :class:`Vector` of two floats. Vectors can be multiplied, subtracted etc.

.. autoclass:: pytemscript.modules.Vector
    :members: set_limits, check_limits, get, set
