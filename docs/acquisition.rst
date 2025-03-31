Image acquisition
=================

The acquisition can become quite cumbersome due to many different cameras from various manufacturers installed on a microscope.
Here we describe supported / tested cameras and explain how they can be controlled by ``pytemscript``

List of tested cameras:

 * Orius CCD (SC200W (830), SC200B (830))
 * Ceta 16M
 * Ceta D
 * Falcon 3EC
 * Falcon 4(i)
 * K2
 * K3

All methods described below return a **16-bit unsigned integer** (equivalent to MRC mode 6) :meth:`~pytemscript.modules.Image` object.
If movies are being acquired asynchronously, their format can be different.

Standard scripting
------------------

Gatan CCD cameras are usually embedded by TFS and can be controlled via standard scripting. This requires both Digital Micrograph
and TIA to be opened as well as the current camera selected in the Microscope User Interface (CCD/TV camera panel).

.. code-block:: python

    microscope = Microscope()
    acq = microscope.acquisition
    img = acq.acquire_tem_image("BM-Orius", AcqImageSize.FULL, exp_time=1.0, binning=2)

.. warning:: If you need to change the camera, after doing so in the Microscope interface, you have to reconnect the microscope client since the COM interface needs to be reinitialised.

For Gatan K2/K3 cameras (if they are embedded by TFS), standard scripting can only return unaligned average image,
there are no options to acquire movies or change the mode (linear/counting).
You can only modify binning or exposure time.

TecnaiCCD plugin
----------------

FEI has created their own plugin for Gatan CCD cameras. The plugin needs to be installed on Gatan PC inside Digital Micrograph.
Digital Micrograph and TIA need to be opened as well as the current camera selected in the Microscope User Interface (CCD/TV camera panel).
The advantage of this method over standard scripting is ~20 % speed improvement for both acquisition and image return, because the plugin
interacts directly with Digital Micrograph and does not return the image to TIA.

.. code-block:: python

    microscope = Microscope(useTecnaiCCD=True)
    acq = microscope.acquisition
    img = acq.acquire_tem_image("BM-Orius", AcqImageSize.FULL, exp_time=1.0, binning=2, use_tecnaiccd=True)

SerialEMCCD plugin
------------------

David Mastronarde has created a SerialEM `plugin <https://github.com/mastcu/SerialEMCCD>`_ to control both Gatan CCDs and advanced cameras like K2 or K3.
The plugin has to be installed on Gatan PC inside Digital Micrograph, which is normally done during SerialEM installation.
The connection to the plugin is established via a socket interface created by ``pytemscript`` (same way as Leginon does it).
Digital Micrograph needs to be opened. SerialEM does not have to be running.

The plugin provides multiple options for movie acquisition, frame alignment etc.

.. warning:: In development, not available yet

Advanced scripting
------------------

This scripting interface was developed by TFS for their newer cameras like Ceta and Falcon.
The currently supported cameras are Ceta 1, Ceta 2, Falcon 3 and Falcon 4(i).
The interface includes new features like movie acquisition, counting mode, EER format etc.
Movies are offloaded asynchronously to the storage server, while the returned image is an average (aligned or not).

There's no need to open TIA or select the camera in the microscope interface.

See details for :meth:`~pytemscript.modules.Acquisition.acquire_tem_image`

.. code-block:: python

    microscope = Microscope()
    acq = microscope.acquisition
    img = acq.acquire_tem_image("BM-Falcon", AcqImageSize.FULL, exp_time=5.0, binning=1, electron_counting=True, align_image=True, group_frames=2)

.. note:: Advanced scripting features like "Camera Electron Counting" and "Camera Dose Fractions" require separate licenses from TFS.

Speed up the acquisition
------------------------

By default, ``pytemscript`` will use `AsSafeArray` method to convert the COM image object to a numpy array via standard or advanced scripting.
Depending on the image size this method can be very slow (several seconds). There's a trick to save the image object to a temporary file
(`AsFile` COM method) and then read it, which seems to work much faster (up to 3x). However, this requires an extra `imageio` dependency for reading the temporary file.

.. warning:: On some systems, saving to a file fails with a COM error due to incomplete implementation, so you will have to stick to the default `AsSafeArray` method.

If you want to try this method, add `use_asfile=True` to your acquisition command:

.. code-block:: python

    microscope = Microscope()
    acq = microscope.acquisition
    img = acq.acquire_tem_image("BM-Falcon", AcqImageSize.FULL, exp_time=5.0, use_asfile=True)


STEM acquisition
----------------

STEM detectors have to be embedded by FEI and selected in the Microscope User Interface (STEM user panel). They are controlled by standard scripting.

.. note:: Be aware that the acquisition starts immediately without waiting for detector insertion to finish. It's probably better to manually insert them first in the microscope interface.
