try:
    import grpc
    from google.protobuf import json_format
except ImportError:
    raise ImportError("Missing dependencies, please run 'pip install pytemscript[utapi]'")

from ..utils.misc import setup_logging
from .base_client import BasicClient


class UTAPIClient(BasicClient):
    """ Remote UTAPI client interface for the microscope.

        :param host: Remote hostname or IP address
        :type host: str
        :param port: Remote port number
        :type port: int
        :param debug: Print debug messages
        :type debug: bool
        """
    def __init__(self,
                 host: str = "127.0.0.1",
                 port: int = 46699,
                 debug: bool = False):
        setup_logging("utapi_client.log", prefix="[CLIENT]", debug=debug)

        try:
            self.channel = grpc.insecure_channel('%s:%d' % (host, port))
            self.stub = my_grpc_pb2_grpc.MyServiceStub(self.channel)
        except Exception as e:
            raise RuntimeError("Error communicating with UTAPI server: %s" % e)

    def call_method(self, method_name, *args, **kwargs):
        # Serialize args and kwargs and call the appropriate gRPC method
        request = my_grpc_pb2.MyRequest(method_name=method_name, args=args, kwargs=kwargs)
        response = self.stub.CallMethod(request)
        return response.result
