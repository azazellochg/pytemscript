from typing import List, Optional
import argparse
import platform
import signal


def handle_signal(server):
    """Signal handler to stop the server gracefully."""

    def signal_handler(sig, frame):
        server.stop()

    return signal_handler


def main(argv: Optional[List] = None) -> None:
    parser = argparse.ArgumentParser(
        description="This server should be started on the microscope PC",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-t", "--type", type=str,
                        choices=["socket", "zmq", "grpc"],
                        default="socket",
                        help="Server type to use: socket, zmq or grpc")
    parser.add_argument("-p", "--port", type=int,
                        default=39000,
                        help="Specify port on which the server is listening")
    parser.add_argument("--host", type=str, default='',
                        help="Specify host address on which the server is listening")
    parser.add_argument("--useLD", dest="useLD",
                        default=False, action='store_true',
                        help="Connect to LowDose server on microscope PC (limited control only)")
    parser.add_argument("--useTecnaiCCD", dest="useTecnaiCCD",
                        default=False, action='store_true',
                        help="Connect to TecnaiCCD plugin on microscope PC that controls "
                             "Digital Micrograph (may be faster than via TIA / std scripting)")
    parser.add_argument("-d", "--debug", dest="debug",
                        default=False, action='store_true',
                        help="Enable debug mode")
    args = parser.parse_args(argv)

    if platform.system() != "Windows":
        raise NotImplementedError("This server should be started on the microscope PC (Windows only)")

    if args.type == 'grpc':
        from .grpc_server import serve
        server = serve(args)
        server.start()
        server.wait_for_termination()
    elif args.type == 'zmq':
        from .zmq_server import ZMQServer
        server = ZMQServer(args)
        signal.signal(signal.SIGINT, handle_signal(server))
        server.start()
    elif args.type == 'socket':
        from .socket_server import SocketServer
        server = SocketServer(args)
        signal.signal(signal.SIGINT, handle_signal(server))
        server.start()
