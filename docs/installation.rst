Installation
============

Prerequisites for the FEI or Thermo Fisher Scientific microscope:

    * TEM Scripting
    * TEM Advanced scripting (optional)
    * LowDose (optional)
    * TecnaiCCD plugin for Digital Micrograph (optional)
    * SerialEMCCD plugin for Digital Micrograph (optional)

Requirements for this package:

    * python 3.4 or newer
    * comtypes
    * mrcfile (to save MRC files)
    * numpy
    * pillow (to save non-MRC files)
    * imageio (optional, to speed up image acquisition)

Online installation on Windows
##############################

This assumes you have connection to the Internet. Execute from the command line
(assuming you have your Python interpreter in the path):

.. code-block:: python

    py -m pip install --upgrade pip
    py -m pip install pytemscript

Offline installation on Windows 7 or 10
#######################################

The command below will download pytemscript and its dependencies on a computer connected to the Internet. We assume your microscope PC runs Windows 7 or Windows 10
64-bit OS. You need to know the Python version on the microscope PC (example below is for 3.8):

.. code-block:: python

    pip download -d . pytemscript --python-version 38 --only-binary=:all: --platform win_amd64

Copy downloaded \*.whl files to the target PC and install them:

.. code-block:: python

    py -m pip install pytemscript --no-index --find-links .

If you want to install pytemscript from sources instead, download them from GitHub. You will still need the wheel files for dependencies:

.. code-block:: python

    py -m pip install numpy comtypes mrcfile pillow --no-index --find-links .
    py -m pip install -e <source_directory>

Installation on Linux
#####################

This assumes you want to setup a remote client and have already installed pytemscript on the microscope PC (Windows)
which will run a `server <remote.html>`_. The installation commands are the same as above:

.. code-block:: python

    pip install pytemscript

Installation on Windows XP 32-bit
#################################

Latest supported Python version on Windows XP is 3.4. Download pytemscript and its dependencies on a computer connected to the Internet:

.. code-block:: python

    pip download -d . pytemscript comtypes==1.2.1 mrcfile==1.3.0 numpy==1.15.4 pillow==5.3.0 typing --python-version 34 --only-binary=:all: --platform win32

Copy downloaded \*.whl files to the target PC and install them:

.. code-block:: python

    py -m pip install pytemscript typing --no-index --find-links .

Testing
-------

The package provides a few command-line scripts to test the microscope interface connection and image acquisition:

.. code-block:: python

    pytemscript-test
    pytemscript-test-acquisition
    pytemscript-test-events
