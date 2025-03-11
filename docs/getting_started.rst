Getting started
===============

To begin using **pytemscript**, you should import the client and enumerations:

.. code-block:: python

    from pytemscript.microscope import Microscope
    from pytemscript.utils.enums import *

Next, connect to the instrument by creating a microscope object:

.. code-block:: python

    microscope = Microscope()

The main object provides a couple of general properties:

.. code-block:: python

    microscope.family
    >> "TECNAI"

    microscope.condenser_system
    >> "TWO_CONDENSER_LENSES"

The :meth:`~pytemscript.microscope.Microscope` class has several attributes for each subsystem, e.g.:

.. code-block:: python

    optics = microscope.optics
    illum = optics.illumination
    proj = optics.projection
    stage = microscope.stage
    acq = microscope.acquisition

Each subsystem has its own attributes and methods, consult the `documentation <components/microscope.html>`_ for the full API description.
Below are just a few examples:

.. code-block:: python

    print(microscope.temperature.temp_holder)
    >> 80.5
    microscope.vacuum.run_buffer_cycle()
    microscope.autoloader.load_cartridge(5)
    microscope.stage.move_to(x=+2,y=-1, relative=True)

    from pytemscript.modules import Vector
    vector = Vector(0.03, 0.02)
    microscope.optics.illumination.beam_shift = vector

To see the list of available detectors and cameras:

.. code-block:: python

    microscope.acquisition.cameras
    >> {'BM-Orius': {'supports_csa': False, 'supports_cca': False, 'height': 2048, 'width': 2048,
    >> 'pixel_size(um)': (7.3999999585794285, 7.3999999585794285), 'binnings': [1, 2, 4],
    >> 'shutter_modes': ['POST_SPECIMEN'], 'pre_exposure_limits(s)': (0.0, 0.0),
    >> 'pre_exposure_pause_limits(s)': (0.0, 0.0)}}

    microscope.acquisition.stem_detectors
    >> {'BF': {'binnings': [1, 2, 4, 8]}}

Example of TEM image acquisition is shown below:

.. code-block:: python

    image = microscope.acquisition.acquire_tem_image("BM-Falcon",
                                                     size=AcqImageSize.FULL,
                                                     exp_time=3.0,
                                                     binning=1,
                                                     align_image=True,
                                                     electron_counting=True,
                                                     save_frames=True,
                                                     group_frames=2)
    print(image.timestamp)
    >> '2024:05:20 17:04:18'
    print(image.metadata)
    >> {'width': 4096, 'height': 4096, 'bit_depth': 16, 'pixel_type': 'SIGNED_INT'}
    image.save("file.mrc")

To close the connection, use the method below:

.. code-block:: python

    microscope.disconnect()
