import numpy as np
import socket
import json
from http.client import HTTPConnection
from urllib.parse import urlencode, quote_plus

from .base_microscope import BaseMicroscope


class RequestJsonEncoder(json.JSONEncoder):
    """JSONEncoder which handles iterables and numpy types"""
    def default(self, obj):
        if isinstance(obj, np.generic):
            return obj.item()
        try:
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return super(RequestJsonEncoder, self).default(obj)


class RemoteMicroscope(BaseMicroscope):
    """
    Microscope-like class, which connects to a remote microscope server.

    :param address: (host, port) combination for the remote microscope.
    :param transport: Underlying transport protocol, either 'JSON' (default) or 'PICKLE'
    """
    def __init__(self, address, transport=None, timeout=None):
        self.address = address
        self.timeout = timeout
        self._conn = None
        if transport is None:
            transport = "JSON"
        if transport == "JSON":
            self.accepted_content = ["application/json"]
        elif transport == "PICKLE":
            self.accepted_content = ["application/python-pickle"]
        else:
            raise ValueError("Unknown transport protocol.")

        # Make connection
        self._conn = HTTPConnection(self.address[0], self.address[1], timeout=self.timeout)
        version_string = self.get_version()
        if int(version_string.split('.')[0]) < 2:
            raise ValueError("Expected microscope server version >= 2.0.0, actual version is %s" % version_string)

    def _request(self, method, endpoint, body=None, query=None, headers=None, accepted_response=None):
        """
        Send request to server.

        If accepted_response is None, 200 is accepted for all methods, additionally 204 is accepted
        for methods, which pass a body (PUT, PATCH, POST)

        :param method: HTTP method to use, e.g. "GET" or "PUT"
        :type method: str
        :param endpoint: URL to request
        :type endpoint: str
        :param query: Optional dict or iterable of key-value-tuples to encode as query
        :type: Union[Dict[str, str], Iterable[Tuple[str, str]], None]
        :param body: Body to send
        :type body: Optional[Union[str, bytes]]
        :param headers: Optional dict of additional headers.
        :type headers: Optional[Dict[str, str]]
        :param accepted_response: Accepted response codes
        :type accepted_response: Optional[List[int]]

        :returns: response, decoded response body
        """
        if accepted_response is None:
            accepted_response = [200]
            if method in ["PUT", "PATCH", "POST"]:
                accepted_response.append(204)

        # Create request
        headers = dict(headers) if headers is not None else dict()
        if "Accept" not in headers:
            headers["Accept"] = ",".join(self.accepted_content)
        if "Accept-Encoding" not in headers:
            headers["Accept-Encoding"] = "gzip"
        if query is not None:
            url = endpoint + '?' + urlencode(query)
        else:
            url = endpoint
        self._conn.request(method, url, body, headers)

        # Get response
        try:
            response = self._conn.getresponse()
        except socket.timeout:
            self._conn.close()
            self._conn = None
            raise

        if response.status not in accepted_response:
            if response.status == 404:
                raise KeyError("Failed remote call: %s" % response.reason)
            else:
                raise RuntimeError("Remote call returned status %d: %s" % (response.status, response.reason))
        if response.status == 204:
            return response, None

        # Decode response
        content_length = int(response.getheader("Content-Length", -1))
        encoded_body = response.read(content_length)
        content_type = response.getheader("Content-Type")
        if content_type not in self.accepted_content:
            raise ValueError("Unexpected response type: %s", content_type)
        if response.getheader("Content-Encoding") == "gzip":
            import zlib
            encoded_body = zlib.decompress(encoded_body, wbits=16 + zlib.MAX_WBITS)
        if content_type == "application/json":
            body = json.loads(encoded_body.decode("utf-8"))
        elif content_type == "application/python-pickle":
            import pickle
            body = pickle.loads(encoded_body)
        else:
            raise ValueError("Unsupported response type: %s", content_type)
        return response, body

    def _request_with_json_body(self, method, url, body, query=None, headers=None, accepted_response=None):
        """
        Like :meth:`_request` but body is encoded as JSON.

        ..see :: :meth:`_request`
        """
        if body:
            headers = dict(headers) if headers is not None else dict()
            headers["Content-Type"] = "application/json"
            encoder = RequestJsonEncoder()
            encoded_body = encoder.encode(body).encode("utf-8")
        else:
            encoded_body = None
        return self._request(method, url, body=encoded_body, query=query, headers=headers, accepted_response=accepted_response)

    def get_family(self):
        return self._request("GET", "/v1/family")[1]

    def get_microscope_id(self):
        return self._request("GET", "/v1/microscope_id")[1]

    def get_version(self):
        return self._request("GET", "/v1/version")[1]

    def get_voltage(self):
        return self._request("GET", "/v1/voltage")[1]

    def get_vacuum(self):
        return self._request("GET", "/v1/vacuum")[1]

    def get_stage_holder(self):
        return self._request("GET", "/v1/stage_holder")[1]

    def get_stage_status(self):
        return self._request("GET", "/v1/stage_status")[1]

    def get_stage_limits(self):
        return self._request("GET", "/v1/stage_limits")[1]

    def get_stage_position(self):
        return self._request("GET", "/v1/stage_position")[1]

    def _set_stage_position(self, pos=None, method="GO", speed=None):
        query = {}
        if method is not None:
            query['method'] = method
        if speed is not None:
            query['speed'] = speed
        self._request_with_json_body("PUT", "/v1/stage_position", body=pos, query=query)

    def get_cameras(self):
        return self._request("GET", "/v1/cameras")[1]

    def get_stem_detectors(self):
        return self._request("GET", "/v1/stem_detectors")[1]

    def get_camera_param(self, name):
        return self._request("GET", "/v1/camera_param/" + quote_plus(name))[1]

    def set_camera_param(self, name, values, ignore_errors=None):
        query = None
        if ignore_errors is not None:
            query = {'ignore_errors': int(ignore_errors)}
        self._request_with_json_body("PUT", "/v1/camera_param/" + quote_plus(name), values, query=query)

    def get_stem_detector_param(self, name):
        return self._request("GET", "/v1/stem_detector_param/" + quote_plus(name))[1]

    def set_stem_detector_param(self, name, values, ignore_errors=None):
        query = None
        if ignore_errors is not None:
            query = {'ignore_errors': int(ignore_errors)}
        self._request_with_json_body("PUT", "/v1/stem_detector_param/" + quote_plus(name), values, query=query)

    def get_stem_acquisition_param(self):
        return self._request("GET", "/v1/stem_acquisition_param")[1]

    def set_stem_acquisition_param(self, values, ignore_errors=None):
        if ignore_errors is not None:
            query = {'ignore_errors': int(ignore_errors)}
        else:
            query = None
        self._request_with_json_body("PUT", "/v1/stem_acquisition_param", values, query=query)

    allowed_types = {"INT8", "INT16", "INT32", "INT64", "UINT8", "UINT16", "UINT32", "UINT64", "FLOAT32", "FLOAT64"}
    allowed_endianness = {"LITTLE", "BIG"}

    def acquire(self, *detectors):
        query = tuple(("detectors", det) for det in detectors)
        response, body = self._request("GET", "/v1/acquire", query=query)
        if response.getheader("Content-Type") == "application/json":
            # Unpack array
            import sys
            import base64
            endianness = sys.byteorder.upper()
            result = {}
            for k, v in body.items():
                shape = int(v["height"]), int(v["width"])
                if v["type"] not in self.allowed_types:
                    raise ValueError("Unsupported array type in JSON stream: %s" % str(v["type"]))
                if v["endianness"] not in self.allowed_endianness:
                    raise ValueError("Unsupported endianness in JSON stream: %s" % str(v["endianness"]))
                dtype = np.dtype(v["type"].lower())
                if v["encoding"] == "BASE64":
                    data = base64.b64decode(v["data"])
                else:
                    raise ValueError("Unsupported encoding of array in JSON stream: %s" % str(v["encoding"]))
                data = np.frombuffer(data, dtype=dtype).reshape(*shape)
                if v["endianness"] != endianness:
                    data = data.byteswap()
                result[k] = data
            body = result
        return body

    def get_image_shift(self):
        return self._request("GET", "/v1/image_shift")[1]

    def set_image_shift(self, pos):
        self._request_with_json_body("PUT", "/v1/image_shift", pos)

    def get_beam_shift(self):
        return self._request("GET", "/v1/beam_shift")[1]

    def set_beam_shift(self, pos):
        self._request_with_json_body("PUT", "/v1/beam_shift", pos)

    def get_beam_tilt(self):
        return self._request("GET", "/v1/beam_tilt")[1]

    def set_beam_tilt(self, pos):
        self._request_with_json_body("PUT", "/v1/beam_tilt", pos)

    def normalize(self, mode="ALL"):
        self._request_with_json_body("PUT", "/v1/normalize", mode)

    def get_projection_sub_mode(self):
        return self._request("GET", "/v1/projection_sub_mode")[1]

    def get_projection_mode(self):
        return self._request("GET", "/v1/projection_mode")[1]

    def set_projection_mode(self, mode):
        self._request_with_json_body("PUT", "/v1/projection_mode", mode)

    def get_projection_mode_string(self):
        return self._request("GET", "/v1/projection_mode_string")[1]

    def get_magnification_index(self):
        return self._request("GET", "/v1/magnification_index")[1]

    def set_magnification_index(self, index):
        self._request_with_json_body("PUT", "/v1/magnification_index", index)

    def get_indicated_camera_length(self):
        return self._request("GET", "/v1/indicated_camera_length")[1]

    def get_indicated_magnification(self):
        return self._request("GET", "/v1/indicated_magnification")[1]

    def get_defocus(self):
        return self._request("GET", "/v1/defocus")[1]

    def set_defocus(self, value):
        self._request_with_json_body("PUT", "/v1/magnification_index", value)

    def get_objective_excitation(self):
        return self._request("GET", "/v1/objective_excitation")[1]

    def get_intensity(self):
        return self._request("GET", "/v1/intensity")[1]

    def set_intensity(self, value):
        self._request_with_json_body("PUT", "/v1/intensity", value)

    def get_objective_stigmator(self):
        return self._request("GET", "/v1/objective_stigmator")[1]

    def set_objective_stigmator(self, value):
        self._request_with_json_body("PUT", "/v1/objective_stigmator", value)

    def get_condenser_stigmator(self):
        return self._request("GET", "/v1/condenser_stigmator")[1]

    def set_condenser_stigmator(self, value):
        self._request_with_json_body("PUT", "/v1/condenser_stigmator", value)

    def get_diffraction_shift(self):
        return self._request("GET", "/v1/diffraction_shift")[1]

    def set_diffraction_shift(self, value):
        self._request_with_json_body("PUT", "/v1/diffraction_shift", value)

    def get_state(self):
        return self._request("GET", "/v1/state")[1]
