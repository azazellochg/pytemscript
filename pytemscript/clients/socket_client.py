import logging
import socket
import pickle
from typing import Dict


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
        self.client_socket = None

        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,
                            datefmt='%d/%b/%Y %H:%M:%S',
                            format='[CLIENT] [%(asctime)s] %(message)s',
                            handlers=[
                                logging.FileHandler("socket_client.log", "w", "utf-8"),
                                logging.StreamHandler()])
        try:
            self.client_socket = socket.create_connection((self.host, self.port),
                                                          timeout=5)
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
            logging.debug("Received response: %s" % response)
            return response

        if method_name in ["cache", "has_advanced_iface",
                           "has_lowdose_iface", "has_ccd_iface"]:
            # for properties, execute immediately
            return method_or_property()

        return method_or_property

    def __send_request(self, payload: Dict):
        """ Send data to the remote server and return response. """
        serialized_data = pickle.dumps(payload)
        length = len(serialized_data)
        logging.debug("Sending request: %s bytes, %s" % (length, payload))
        self.client_socket.sendall(length.to_bytes(4, byteorder="big") + serialized_data)

        length_bytes = self.client_socket.recv(4)
        length = int.from_bytes(length_bytes, byteorder='big')

        response_data = self.client_socket.recv(length)
        if not response_data:
            raise ConnectionError("No response received from server")

        return pickle.loads(response_data)

    def disconnect(self):
        """ Disconnect from the remote server. """
        self.client_socket.close()
        self.client_socket = None
