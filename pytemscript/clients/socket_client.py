import logging
import socket
import pickle
from typing import Dict

from pytemscript.utils.misc import setup_logging, send_data, receive_data


class SocketClient:
    """ Remote socket client interface for the microscope.

    :param host: Remote hostname or IP address
    :type host: str
    :param port: Remote port number
    :type port: int
    :param debug: Print debug messages
    :type debug: bool
    """
    def __init__(self,
                 host: str = "127.0.0.1",
                 port: int = 39000,
                 debug: bool = False):
        self.host = host
        self.port = port
        self.socket = None

        setup_logging("socket_client.log", prefix="[CLIENT]", debug=debug)
        try:
            self.socket = socket.create_connection((self.host, self.port),
                                                   timeout=5)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except Exception as e:
            raise RuntimeError("Error communicating with server: %s" % e)

    def __getattr__(self, method_name: str):
        """ This handles both method calls and properties of the Microscope client instance. """
        def method_or_property(*args, **kwargs):
            payload = {
                "method": method_name,
                "args": args,
                "kwargs": kwargs
            }
            response = self.__send_request(payload)
            logging.debug("Received response: %s", response)
            return response

        if method_name in ["cache", "has_advanced_iface",
                           "has_lowdose_iface", "has_ccd_iface"]:
            # for properties, execute immediately
            return method_or_property()

        return method_or_property

    def __send_request(self, payload: Dict):
        """ Send data to the remote server and return response. """
        data = pickle.dumps(payload)
        logging.debug("Sending request: %s", payload)
        send_data(self.socket, data)

        response = receive_data(self.socket)

        return pickle.loads(response)

    def disconnect(self):
        """ Disconnect from the remote server. """
        self.socket.close()
        self.socket = None
