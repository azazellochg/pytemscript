#!/usr/bin/env python3
from setuptools import setup, find_packages
# To use a consistent encoding
from codecs import open
from os import path
import sys
from pytemscript import __version__

here = path.abspath(path.dirname(__file__))
# Long description
with open(path.join(here, "README.rst"), "r", encoding="utf-8") as fp:
    long_description = fp.read()

# Python 3.4 doesn't support certain keywords in setup
if sys.version_info < (3, 5):
    setup(name='pytemscript',
          version=__version__,
          description='TEM Scripting adapter for FEI/TFS microscopes',
          author='Tore Niermann, Grigory Sharov',
          author_email='tore.niermann@tu-berlin.de, gsharov@mrc-lmb.cam.ac.uk',
          long_description=long_description,
          packages=find_packages(),
          platforms=['any'],
          license="GNU General Public License v3 (GPLv3)",
          classifiers=[
              'Development Status :: 4 - Beta',
              'Intended Audience :: Science/Research',
              'Intended Audience :: Developers',
              'Operating System :: OS Independent',
              'Programming Language :: Python :: 3.4',
              'Programming Language :: Python :: 3.8',
              'Programming Language :: Python :: 3.9',
              'Programming Language :: Python :: 3.10',
              'Programming Language :: Python :: 3.11',
              'Programming Language :: Python :: 3.12',
              'Topic :: Scientific/Engineering',
              'Topic :: Software Development :: Libraries',
              'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
          ],
          keywords='TEM python',
          install_requires=[
              "comtypes==1.2.1",
              "mrcfile==1.3.0",
              "numpy==1.15.4",
              "pip<=19.1.1",
              "pillow==5.3.0",
              "setuptools<=12.0.5",
              "typing"
          ],
          extras_require={
              "dev": ["matplotlib", "mypy"],
              "utapi": ["grpcio", "grpcio-tools", "protobuf"]
          },
          entry_points={'console_scripts': [
              'pytemscript-server = pytemscript.server.run:main',
              'pytemscript-test = tests.test_microscope:main',
              'pytemscript-test-acquisition = tests.test_acquisition:main',
              'pytemscript-test-events = tests.test_events:main'
          ]},
          url="https://github.com/azazellochg/pytemscript",
    )

else:
    with open(path.join(here, "requirements.txt")) as f:
        requirements = f.read().splitlines()

    setup(name='pytemscript',
          version=__version__,
          description='TEM Scripting adapter for FEI/TFS microscopes',
          author='Tore Niermann, Grigory Sharov',
          author_email='tore.niermann@tu-berlin.de, gsharov@mrc-lmb.cam.ac.uk',
          long_description=long_description,
          long_description_content_type='text/x-rst',
          packages=find_packages(),
          platforms=['any'],
          license="GNU General Public License v3 (GPLv3)",
          python_requires='>=3.4',
          classifiers=[
              'Development Status :: 4 - Beta',
              'Intended Audience :: Science/Research',
              'Intended Audience :: Developers',
              'Operating System :: OS Independent',
              'Programming Language :: Python :: 3.4',
              'Programming Language :: Python :: 3.8',
              'Programming Language :: Python :: 3.9',
              'Programming Language :: Python :: 3.10',
              'Programming Language :: Python :: 3.11',
              'Programming Language :: Python :: 3.12',
              'Topic :: Scientific/Engineering',
              'Topic :: Software Development :: Libraries',
              'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
          ],
          keywords='TEM python',
          install_requires=[requirements],
          extras_require={
              "extra": ["matplotlib", "mypy"],
              "utapi": ["grpcio", "grpcio-tools", "protobuf"]
          },
          entry_points={'console_scripts': [
              'pytemscript-server = pytemscript.server.run:main',
              'pytemscript-test = tests.test_microscope:main',
              'pytemscript-test-acquisition = tests.test_acquisition:main',
              'pytemscript-test-events = tests.test_events:main'
          ]},
          url="https://github.com/azazellochg/pytemscript",
          project_urls={
              "Source": "https://github.com/azazellochg/pytemscript",
              "Documentation": "https://pytemscript.readthedocs.io/"
          }
    )
