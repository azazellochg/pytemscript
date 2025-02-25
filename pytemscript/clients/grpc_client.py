try:
    import grpc
    import my_grpc_pb2
    import my_grpc_pb2_grpc
except ImportError:
    raise ImportError("Missing dependency 'grpcio', please install it via pip")

from .base_client import BasicClient


class GRPCClient(BasicClient):
    def __init__(self, host, port):
        self.channel = grpc.insecure_channel('%s:%d' % (host, port))
        self.stub = my_grpc_pb2_grpc.MyServiceStub(self.channel)

    def call_method(self, method_name, *args, **kwargs):
        # Serialize args and kwargs and call the appropriate gRPC method
        request = my_grpc_pb2.MyRequest(method_name=method_name, args=args, kwargs=kwargs)
        response = self.stub.CallMethod(request)
        return response.result
