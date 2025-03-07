.. _installation:

Installation
============

.. note:: *Windows XP*: latest available Python is 3.4. *Windows 7*: latest available Python is 3.8

Requirements:

    * python 3.4 or newer
    * comtypes
    * mrcfile (to save MRC files)
    * numpy
    * pillow (to save non-MRC files)

Installation from PyPI on Windows
#################################

This assumes you have connection to the internet. Execute from the command line
(assuming you have your Python interpreter in the path):

.. code-block:: python

    py -m pip install --upgrade pip
    py -m pip install pytemscript

Offline-Installation from wheels file on Windows
################################################

This assumes you have downloaded the wheels file <downloaded-wheels-file>.whl for
temscript and comtypes into the current folder. Execute from the command line
(assuming you have your Python interpreter in the path):

.. code-block:: python

    py -m pip install numpy comtypes mrcfile pytemscript --no-index --find-links .

If you want to install pytemscript from sources (you still need to download comtypes \*.whl):

.. code-block:: python

    py -m pip install numpy comtypes mrcfile --no-index --find-links .
    py -m pip install -e <source_directory>

Installation on Linux
#####################

This assumes you want to setup a remote client and have already installed pytemscript on the microscope PC (Windows)
which will run a :ref:`server <remote>`.
The installation commands are the same as above, just instead of `py -m pip install` simply use `pip install`.

Testing
-------

The package provides a few command-line scripts to test the microscope interface connection and image acquisition:

.. code-block:: python

    pytemscript-test -h
    pytemscript-test-acquisition
