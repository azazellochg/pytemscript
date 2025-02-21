import pickle
try:
    import zmq
except ImportError:
    raise ImportError("Missing dependency 'pyzmq', please install it via pip")

from .base_client import BasicClient


class ZMQClient(BasicClient):
    def __init__(self, host, port):
        self.context = zmq.Context()
        self.sock = self.context.socket(zmq.REQ)  # Request-Reply pattern
        self.sock.connect("tcp://%s:%d" % (host, port))

    def call_method(self, method_name, *args, **kwargs):
        # Serialize the request
        message = pickle.dumps({
            'method': method_name,
            'args': args,
            'kwargs': kwargs
        })
        self.sock.send(message)
        # Receive the response
        response = self.sock.recv()
        return pickle.loads(response)
