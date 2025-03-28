import logging
import sys
import socket
import pickle
from functools import lru_cache
from typing import Dict

from ..utils.misc import setup_logging, send_data, receive_data, RequestBody
from .base_client import BasicClient


class SocketClient(BasicClient):
    """ Remote socket client interface for the microscope.

    :param str host: Remote hostname or IP address
    :param int port: Remote port number
    :param bool debug: Print debug messages
    """
    def __init__(self,
                 host: str = "127.0.0.1",
                 port: int = 39000,
                 debug: bool = False):
        self.host = host
        self.port = port
        self.sock = None

        setup_logging("socket_client.log", prefix="[CLIENT]", debug=debug)
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=5)
            self.sock.settimeout(None)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            if sys.platform == "win32":
                self.sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60 * 1000, 10 * 1000))
                # (enable=1, idle time=60 sec, interval=10 sec)
            else:
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)
        except Exception as e:
            raise RuntimeError("Error communicating with socket server: %s" % e)

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

    @property
    @lru_cache(maxsize=1)
    def has_calgetter_iface(self) -> bool:
        response = self.__send_request({"method": "has_calgetter_iface"})
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
        self.sock.close()
        self.sock = None

    def __send_request(self, payload: Dict):
        """ Send data to the remote server and return response. """
        data = pickle.dumps(payload)
        logging.debug("Sending request: %s", payload)
        send_data(self.sock, data)
        response = receive_data(self.sock)

        return pickle.loads(response)
