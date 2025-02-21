from argparse import Namespace
import pickle
try:
    import zmq
except ImportError:
    raise ImportError("Missing dependency 'pyzmq', please install it via pip")


class ZMQServer:
    def __init__(self, args: Namespace):
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.REP)  # Reply pattern
        host = args.host or "127.0.0.1"
        port = args.port or 5555
        self.useLD = args.useLD
        self.useTecnaiCCD = args.useTecnaiCCD
        self.sock.bind("tcp://%s:%d" % (host, port))

    def start(self):
        while True:
            message = self.sock.recv()
            data = pickle.loads(message)
            method_name = data['method']
            args = data['args']
            kwargs = data['kwargs']
            # Call the appropriate method on the server and send back the result
            result = call_method_on_server_object(method_name, *args, **kwargs)
            self.sock.send(pickle.dumps(result))
