Enumerations
============

Enumerations are represented by :class:`IntEnum` objects and are used to describe integer or string constants.
When a property returns an enumeration, it will print its **name**. When you assign a variable to an enumeration,
it will use its integer **value**.

Example:

.. code-block:: python

    from pytemscript.microscope import Microscope
    from pytemscript.utils.enums import *

    microscope = Microscope()
    stage = microscope.stage
    print(stage.status)
    'READY'  # <-- returns enumeration name

    camera_size = AcqImageSize.FULL  # <-- assigns enumeration value
    image = microscope.acquisition.acquire_tem_image("BM-Ceta",
                                                     size=camera_size,
                                                     exp_time=0.5,
                                                     binning=2)

.. automodule:: pytemscript.utils.enums
    :members:
