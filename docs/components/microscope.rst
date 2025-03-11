Microscope class
================

The :class:`Microscope` class provides a Python interface to the microscope.
Below are the main class properties, each represented by a separate class:

    * acquisition = :meth:`~pytemscript.modules.Acquisition`
    * apertures = :meth:`~pytemscript.modules.Apertures`
    * autoloader = :meth:`~pytemscript.modules.Autoloader`
    * energy_filter = :meth:`~pytemscript.modules.EnergyFilter`
    * gun = :meth:`~pytemscript.modules.Gun`
    * optics = :meth:`~pytemscript.modules.Optics`

        * illumination = :meth:`~pytemscript.modules.Illumination`
        * projection = :meth:`~pytemscript.modules.Projection`

    * piezo_stage = :meth:`~pytemscript.modules.PiezoStage`
    * stage = :meth:`~pytemscript.modules.Stage`
    * stem = :meth:`~pytemscript.modules.Stem`
    * temperature = :meth:`~pytemscript.modules.Temperature`
    * user_buttons = :meth:`~pytemscript.modules.UserButtons`
    * user_door = :meth:`~pytemscript.modules.UserDoor`
    * vacuum = :meth:`~pytemscript.modules.Vacuum`

Example usage
-------------

.. autoclass:: pytemscript.microscope.Microscope
    :members: family, condenser_system, disconnect

Documentation
-------------

.. automodule:: pytemscript.modules
    :members: Acquisition, Apertures, Autoloader, EnergyFilter, Gun, Optics, Illumination, Projection, PiezoStage, Stage, Stem, Temperature, UserButtons, UserDoor, Vacuum
