.. _restrictions:

Restrictions
============

The restrictions listed here are issues with the scripting interface itself. `pytemscript` only provides Python bindings
to this scripting interface, thus these issues also occur using `pytemscript`. As there is no public list of known issues
with the scripting interfaces by FEI or Thermo Fisher Scientific themself, known issues are listed here for the user's
reference.

* On microscopes with just standard scripting only devices which are selected in the Microscope User Interface are available.
* Changing the projection mode from IMAGING to DIFFRACTION and back again changes the magnification in imaging mode (Titan 1.1).
* :attr:`optics.projection.magnification` does not return the actual magnification, but always 0.0 (Titan 1.1)
* Setting the binning value for a CCD camera, changes the exposure time (Titan 1.1 with Gatan US1000 camera).
* Acquisition with changed exposure time with a CCD camera, are not always done with the new exposure time.
* :attr:`optics.illumination.intensity_limit` raises exception when queried (Titan 1.1).
* :meth:`stage.go_to()` fails if movement is performed along multiple axes with speed keyword specified (internally the GoToWithSpeed method if the COM interface fails for multiple axes, Titan 1.1)
* If during a specimen holder exchange no holder is selected (yet), querying :attr:`stage.holder` fails (Titan 1.1).
