from typing import Optional, Any
import os
import functools
import numpy as np
import logging
from hashlib import sha1
from logging.handlers import TimedRotatingFileHandler

from .constants import HEADER_DATA, HEADER_MSG
from .enums import ImagePixelType


def rgetattr(obj, attrname, *args, iscallable=False, log=True, **kwargs):
    """ Recursive getattr or callable on a COM object"""
    try:
        if log:
            logging.debug("<= GET: %s, args=%r, kwargs=%r",
                          attrname, args, kwargs)
        result = functools.reduce(getattr, attrname.split('.'), obj)
        return result(*args, **kwargs) if iscallable else result

    except Exception as e:
        raise AttributeError("%s: %s" % (attrname, e))


def rsetattr(obj, attrname, value):
    """ https://stackoverflow.com/a/31174427 """
    pre, _, post = attrname.rpartition('.')
    return setattr(rgetattr(obj, pre, log=False) if pre else obj, post, value)


def setup_logging(fn: str,
                  prefix: Optional[str] = None,
                  debug: bool = False) -> None:
    """ Setup logging handlers.
    :param str fn: filename
    :param str prefix: prefix for the formatting
    :param bool debug: use debug level instead
    """
    fmt = '[%(asctime)s] %(levelname)s %(message)s'
    if prefix is not None:
        fmt = prefix + fmt

    formatter = logging.Formatter(fmt)

    file_handler = TimedRotatingFileHandler(fn, when="midnight", interval=1, backupCount=7)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO,
                        datefmt='%d/%b/%Y %H:%M:%S',
                        handlers=[file_handler, console_handler])


def send_data(sock, data: bytes, datatype="msg") -> None:
    """ Assemble data packet and send it over socket.
    :param bytes data: raw data
    :param str datatype: data type

    The packet includes the following:
        - header: 2 bytes
        - length of data: 4 bytes
        - checksum: 20 bytes - only if header == HEADER_DATA
        - actual data
    """
    packet = bytearray()
    packet.extend(HEADER_MSG if datatype == "msg" else HEADER_DATA)
    packet.extend(len(data).to_bytes(4, byteorder="big"))

    if datatype == "data": # add checksum
        checksum = sha1(data).digest()
        packet.extend(checksum)

    packet.extend(data)
    sock.sendall(packet)


def receive_data(sock) -> bytes:
    """ Received a packet and extract data. """
    header = sock.recv(6)
    if len(header) == 0:  # client disconnected
        return b''
    elif len(header) != 6:
        raise ConnectionError("Incomplete header received")

    datatype = header[:2]
    rcv_checksum = None
    if datatype == HEADER_DATA:
        rcv_checksum = sock.recv(20)

    data_length = int.from_bytes(header[2:], 'big')

    data = bytearray()
    while len(data) < data_length:
        chunk = sock.recv(data_length - len(data))
        if not chunk:
            raise ConnectionError("Connection lost while receiving data")
        data.extend(chunk)

    if datatype == HEADER_DATA:
        checksum = sha1(data).digest()
        if checksum != rcv_checksum:
            raise ConnectionError("Wrong checksum received")
        logging.debug("Image checksum OK!")

    return data


def convert_image(obj,
                  name: Optional[str] = None,
                  width: Optional[int] = None,
                  height: Optional[int] = None,
                  bit_depth: Optional[int] = None,
                  pixel_size: Optional[float] = None,
                  advanced: Optional[bool] = False,
                  use_asfile: Optional[bool] = False,
                  use_variant: Optional[bool] = False,
                  **kwargs):
    """ Convert COM image object into an uint16 Image.

    :param obj: COM object
    :param str name: optional name for the image
    :param int width: width of the image
    :param int height: height of the image
    :param int bit_depth: bit depth of the image
    :param float pixel_size: pixel size of the image
    :param bool advanced: advanced scripting flag
    :param bool use_asfile: use asfile method
    :param bool use_variant: use variant method
    """
    from pytemscript.modules import Image

    if use_asfile:
        # Save into a temp file and read into numpy
        try:
            import imageio
        except ImportError:
            raise ImportError("imageio library not found, you cannot use "
                              "use_asfile kwarg.")
        fn = r"C:/temp.tif"
        if os.path.exists(fn):
            os.remove(fn)
        obj.SaveToFile(fn) if advanced else obj.AsFile(fn, 0)
        data = imageio.imread(fn).astype("uint16")
        os.remove(fn)

    elif use_variant:
        # TecnaiCCD plugin: obj is a variant, convert to numpy
        # Also, transpose is required to match TIA orientation
        data = np.array(obj, dtype="uint16").T

    else:
        # Convert to a safearray and then to numpy
        from comtypes.safearray import safearray_as_ndarray
        with safearray_as_ndarray:
            # AsSafeArray always returns int32 array
            # Also, transpose is required to match TIA orientation
            data = obj.AsSafeArray.astype("uint16").T

    name = name or obj.Name

    metadata = {
        "width": width or int(obj.Width),
        "height": height or int(obj.Height),
        "bit_depth": 16, # int(bit_depth or (obj.BitDepth if advanced else obj.Depth)),
        "pixel_type": ImagePixelType.UNSIGNED_INT.name # ImagePixelType(obj.PixelType).name if advanced
    }
    if pixel_size is not None:
        metadata["PixelSize.Width"] = pixel_size
        metadata["PixelSize.Height"] = pixel_size
    if advanced:
        metadata.update({item.Key: item.ValueAsString for item in obj.Metadata})
    #if "BitsPerPixel" in metadata:
    #    metadata["bit_depth"] = int(metadata["BitsPerPixel"])

    return Image(data, name, metadata)


class RequestBody:
    """ Dataclass-like structure of a request passed to the client. """
    def __init__(self,
                 attr: Optional[str] = None,
                 validator: Optional[Any] = None,
                 **kwargs) -> None:
        self.attr = attr
        self.validator = validator
        self.kwargs = kwargs

    def __str__(self) -> str:
        return '{"attr": "%s", "validator": "%s", "kwargs": %r}' % (
            self.attr, self.validator, self.kwargs)

    def __repr__(self) -> str:
        return 'RequestBody(attr=%s, validator=%s, kwargs=%r)' % (
            self.attr, self.validator, self.kwargs)
