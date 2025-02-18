import logging
import socket
import pickle
from functools import lru_cache
from typing import Dict

from ..utils.misc import setup_logging, send_data, receive_data, RequestBody
from .base_client import BasicClient


class SocketClient(BasicClient):
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
            self.socket = socket.create_connection((self.host, self.port), timeout=5)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except Exception as e:
            raise RuntimeError("Error communicating with server: %s" % e)

    @property
    @lru_cache(maxsize=1)
    def has_advanced_iface(self) -> bool:
        response = self.__send_request({"method": "has_advanced_iface"})
        logging.debug("Received response: %s", response)

        return response

    @property
    @lru_cache(maxsize=1)
    def has_lowdose_iface(self) -> bool:
        response = self.__send_request({"method": "has_lowdose_iface"})
        logging.debug("Received response: %s", response)

        return response

    @property
    @lru_cache(maxsize=1)
    def has_ccd_iface(self) -> bool:
        response = self.__send_request({"method": "has_ccd_iface"})
        logging.debug("Received response: %s", response)

        return response

    def call(self, method: str, body: RequestBody):
        """ Main method used by modules. """
        payload = {"method": method, "body": body}
        response = self.__send_request(payload)
        logging.debug("Received response: %s", response)

        return response

    def disconnect(self) -> None:
        """ Disconnect from the remote server. """
        self.socket.close()
        self.socket = None

    def __send_request(self, payload: Dict):
        """ Send data to the remote server and return response. """
        data = pickle.dumps(payload)
        logging.debug("Sending request: %s", payload)
        send_data(self.socket, data)
        response = receive_data(self.socket)

        return pickle.loads(response)
