import threading
import time

from pytemscript.microscope import Microscope
from pytemscript.server.run import main as server_run


def test_interface(microscope: Microscope) -> None:
    """ Test remote interface. """
    stage = microscope.stage
    print(stage.position)
    stage.go_to(x=1, y=-1, relative=True)

def test_connection(connection_type: str = "socket") -> None:
    """ Create server and client, then test the connection. """
    print("Testing %s connection" % connection_type)
    if connection_type == "socket":
        port = 39000
    elif connection_type == "grpc":
        port = 50051
    elif connection_type == "zmq":
        port = 5555
    else:
        raise ValueError("Unknown connection type")

    # Start server
    stop_event = threading.Event()
    args = ["-t", connection_type, "-p", port, "--host", "127.0.0.1", "-d"]
    thread = threading.Thread(target=server_run, args=[(args,), stop_event])
    thread.start()
    time.sleep(1)

    # Start client
    client = Microscope(connection=connection_type, host="", port=port, debug=True)
    test_interface(client)

    # Stop server
    stop_event.set()
    thread.join()

def main() -> None:
    """ Basic test to check server-client connection on localhost. """
    test_connection(connection_type="socket")
    #test_connection(connection_type="grpc")
    #test_connection(connection_type="zmq")

if __name__ == '__main__':
    main()
