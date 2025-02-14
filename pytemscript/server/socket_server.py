from argparse import Namespace
import socket
import threading
import pickle
import logging

from pytemscript.utils.misc import setup_logging, send_data, receive_data


class SocketServer:
    """ Simple socket server, each client gets its own thread. Not secure at all. """
    def __init__(self, args: Namespace):
        """ Initialize the basic variables and logging. """
        self.socket = None
        self.server_com = None
        self.host = args.host or "127.0.0.1"
        self.port = args.port or 39000
        self.useLD = args.useLD
        self.useTecnaiCCD = args.useTecnaiCCD

        setup_logging("socket_server.log", prefix="[SERVER]", debug=args.debug)

    def start(self):
        """ Start both the COM client (as a server) and the socket server. """
        from pytemscript.clients.com_client import COMClient
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPALIVE, 10)

        self.socket.bind((self.host, self.port))
        self.socket.listen(5)

        # start COM client as a server
        self.server_com = COMClient(useTecnaiCCD = self.useTecnaiCCD,
                                    useLD=self.useLD,
                                    as_server=True)
        logging.info("Socket server listening on %s:%d",self.host, self.port)
        try:
            while True:
                client_socket, client_address = self.socket.accept()
                client_socket.settimeout(None)  # Remove timeout for persistent connection
                # each client in a separate thread
                thread = threading.Thread(target=self.handle_client,
                                          args=(client_socket, client_address))
                thread.start()

        except KeyboardInterrupt:
            logging.info("Ctrl+C received. Server shutting down..")

        finally:
            self.socket.close()
            # explicitly stop the COM server
            self.server_com._scope._close()
            self.server_com = None

    def handle_client(self, client_socket, client_address):
        """ Handle client requests in a loop until the client disconnects. """
        logging.info("New connection from: %s", client_address)
        try:
            while True:
                data = receive_data(client_socket)
                message = pickle.loads(data)
                method_name = message['method']
                args = message['args']
                kwargs = message['kwargs']
                logging.debug("Received request: %s, args: %s, kwargs: %s",
                              method_name, args, kwargs)

                # Call the appropriate method and send back the result
                result = self.handle_request(method_name, *args, **kwargs)
                logging.debug("Sending response: %s", result)
                response = pickle.dumps(result)
                send_data(client_socket, response)

        except socket.error as e:
            logging.error(e)

        except KeyboardInterrupt:
            raise

        finally:
            client_socket.close()
            logging.info("Client %s disconnected", client_address)

    def handle_request(self, method_name: str, *args, **kwargs):
        """ Process a socket message: pass method to the COM server
         and return result to the client. """
        method = getattr(self.server_com, method_name, None)
        if method is None:
            raise ValueError("Unknown method: %s" % method_name)
        elif callable(method):
            return method(*args, **kwargs)
        else:  # for property decorators
            return method
