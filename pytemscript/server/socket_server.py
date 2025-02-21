from argparse import Namespace
import socket
import pickle
import logging
from typing import Optional

from ..modules.extras import Image
from ..utils.misc import setup_logging, send_data, receive_data, RequestBody


class SocketServer:
    """ Simple socket server, each client gets its own thread. Not secure at all. """
    def __init__(self, args: Namespace):
        self.sock = None
        self.server_com = None
        self.host = args.host or "127.0.0.1"
        self.port = args.port or 39000
        self.useLD = args.useLD
        self.useTecnaiCCD = args.useTecnaiCCD
        self.running = True

        setup_logging("socket_server.log", prefix="[SERVER]", debug=args.debug)

    def start(self):
        """ Start both the COM client (as a server) and the socket server. """
        from pytemscript.clients.com_client import COMClient
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_socket_options()
        self.sock.bind((self.host, self.port))
        self.sock.listen(1)
        self.sock.settimeout(1)

        # start COM client as a server
        self.server_com = COMClient(useTecnaiCCD = self.useTecnaiCCD,
                                    useLD=self.useLD,
                                    as_server=True)
        logging.info("Socket server listening on %s:%d",self.host, self.port)

        while self.running:
            try:
                client_socket, client_address = self.sock.accept()
                logging.info("New connection from: %s", client_address)
                client_socket.settimeout(None)  # Remove timeout for persistent connection
                self.handle_client(client_socket, client_address)

            except socket.timeout:
                continue

        logging.info("Stopping server...")
        self.cleanup()

    def stop(self):
        """ Stop the server. """
        self.running = False
        self.cleanup()

    def cleanup(self):
        """ Graceful exit. """
        self.sock.close()
        # explicitly stop the COM server
        if self.server_com is not None:
            self.server_com._scope._close()
            self.server_com = None

    def handle_client(self, client_socket, client_address):
        """ Handle client requests in a loop until the client disconnects. """
        try:
            while self.running:
                data = receive_data(client_socket)
                if not data:
                    break # client disconnected
                message = pickle.loads(data)
                logging.debug("Received request: %s", message)
                method = message.get('method')
                body = message.get('body')

                # Call the appropriate method and send back the result
                result = self.handle_request(method, body)
                logging.debug("Sending response: %s", result)
                response = pickle.dumps(result)

                datatype = "data" if isinstance(result, Image) else "msg"
                send_data(client_socket, response, datatype)

        except Exception as e:
            logging.error("Client %s error: %s", client_address, e)

        finally:
            client_socket.close()
            logging.info("Client %s disconnected", client_address)

    def handle_request(self,
                       method: str,
                       body: Optional[RequestBody] = None):
        """ Process a socket message: pass method to the COM server
         and return result to the client. """
        try:
            if body is None: # it is a property
                return getattr(self.server_com, method)
            else:
                return self.server_com.call(method, body)
        except (AttributeError, ValueError):
            return "ERROR"

    def set_socket_options(self):
        """ Extra options for the socket connection. """
        self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 60 * 1000, 10 * 1000))  # (enable, time(ms), interval(ms))
