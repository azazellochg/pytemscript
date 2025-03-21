Remote execution
================

Two options are available to execute the API commands remotely:

 * socket-based server and client
 * UTAPI client

Socket-based client
-------------------

In this mode the pytemscript socket server must run on the microscope PC (Windows).
By default, it will listen for clients on port 39000.

.. danger::

    The server provides no means of security or authorization control itself.
    Thus it is highly recommended to let the server only listen to internal networks or at least route it through a reverse proxy, which implements sufficient security.

To launch the server, simply run ``pytemscript-server`` command:

.. code-block:: none

    usage: pytemscript-server [-h] [-p PORT] [--host HOST] [--useLD] [--useTecnaiCCD] [-d]

    optional arguments:
    -h, --help                      show this help message and exit
    -p, --port PORT                 Specify port on which the server is listening (default: 39000)
    --host HOST                     Specify host address on which the server is listening (default: 127.0.0.1)
    --useLD                         Connect to LowDose server on microscope PC (limited control only) (default: False)
    --useTecnaiCCD                  Connect to TecnaiCCD plugin on microscope PC that controls Digital Micrograph (may be faster than via TIA / std scripting) (default: False)
    -d, --debug                     Enable debug mode (default: False)

Then you can connect to the server as shown below:

.. code-block:: python

    from pytemscript.microscope import Microscope
    microscope = Microscope(connection="socket", host="127.0.0.1", port=39000)
    ...
    microscope.disconnect()

Diagnostic messages are saved to ``socket_client.log`` and ``socket_server.log`` as well as printed to the console. Log files are rotated weekly at midnight.

To shutdown pytemscript-server, press Ctrl+C in the server console.

UTAPI client
------------

.. warning:: Under development, currently not available

TFS is actively developing new (licensed) UTAPI interface that is aimed to eventually replace both standard and
advanced scripting. It is only available for TEM server version 7.18 and newer. To verify,
you can search for ``utapi_server.exe`` in the Task Manager. The server is listening for clients on port
**46699**. Under the hood UTAPI utilizes gRPC (Google Remote Procedure Calls) framework that uses protocol
buffers for communication.

Pytemscript converts its API commands to UTAPI calls. The client only supports Python 3.8+ and requires
a few extra dependencies to be installed:

.. code-block:: python

    py -m pip install pytemscript[utapi]

You can connect using UTAPI client as shown below:

.. code-block:: python

    from pytemscript.microscope import Microscope
    microscope = Microscope(connection="utapi", host="192.168.0.1")
    ...
    microscope.disconnect()

Diagnostic messages are saved to ``utapi_client.log`` as well as printed to the console. Log files are rotated weekly at midnight.
