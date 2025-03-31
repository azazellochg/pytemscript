Introduction
------------

``Pytemscript`` is a Python package designed around standard and advanced scripting
interfaces of Thermo Fisher Scientific and FEI transmission electron microscopes. The functionality is
limited to the functionality of the original COM scripting interfaces. For detailed information
about TEM scripting see the documentation accompanying your microscope.

The ``pytemscript`` package provides a client API to connect both locally and remotely to the microscope PC.
Currently, the minimum supported Python version is 3.4, so you should be able to control TEM instruments
operating Windows XP or newer OS. This allows us to support scripting on a wide range of TEM platforms
including Tecnai, Talos and Titan.

This is a GPL fork of the original BSD-licensed project: https://github.com/niermann/temscript
New changes and this whole product is distributed under either version 3 of the GPL License, or
(at your option) any later version.

Documentation
-------------

The source code is available at https://github.com/azazellochg/pytemscript

The documentation can be found at https://pytemscript.readthedocs.io

.. toctree::
   :maxdepth: 1

   self
   installation
   components/index
   getting_started
   acquisition
   remote
   changelog

Quick example
-------------

Execute this on the microscope PC to create an instance of the local :meth:`~pytemscript.microscope.Microscope`:

.. code-block:: python

    from pytemscript.microscope import Microscope
    microscope = Microscope()

Show the current acceleration voltage:

.. code-block:: python

    microscope.gun.voltage
    300.0

Move beam:

.. code-block:: python

    shift = microscope.optics.illumination.beam_shift
    shift += (0.4, 0.2)
    shift *= 2
    microscope.optics.illumination.beam_shift = shift

Take an image:

.. code-block:: python

    image = microscope.acquisition.acquire_tem_image("BM-Ceta",
                                                     size=AcqImageSize.FULL,  # <-- see enumerations
                                                     exp_time=0.5,
                                                     binning=2)
    image.save("img.mrc")

Disclaimer
----------

Copyright (c) 2012-2021 by Tore Niermann
Contact: tore.niermann (at) tu-berlin.de

Copyright (c) 2022-2025 by Grigory Sharov
Contact: gsharov (at) mrc-lmb.cam.ac.uk

All product and company names are trademarks or registered trademarks
of their respective holders. Use of them does not imply any affiliation
with or endorsement by them.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
