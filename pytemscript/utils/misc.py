from typing import Optional, Any
import functools
import logging
from hashlib import sha1
from logging.handlers import TimedRotatingFileHandler

from .constants import HEADER_DATA, HEADER_MSG
from .enums import ImagePixelType


def rgetattr(obj, attrname, *args, iscallable=False, log=True, **kwargs):
    """ Recursive getattr or callable on a COM object"""
    try:
        if log:
            logging.debug("<= GET: %s, args=%s, kwargs=%s",
                          attrname, args, kwargs)
        result = functools.reduce(getattr, attrname.split('.'), obj)
        return result(*args, **kwargs) if iscallable else result

    except Exception as e:
        raise AttributeError("%s: %s" % (attrname, e))


def rsetattr(obj, attrname, value):
    """ https://stackoverflow.com/a/31174427 """
    pre, _, post = attrname.rpartition('.')
    return setattr(rgetattr(obj, pre, log=False) if pre else obj, post, value)


def setup_logging(fn,
                  prefix: Optional[str] = None,
                  debug: bool = False) -> None:
    """ Setup logging handlers.
    :param fn: filename
    :param prefix: prefix for the formatting
    :param debug: use debug level instead
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
    type: 2 bytes
    length of data: 4 bytes
    checksum: 20 bytes - only if type is "data"
    data: bytes
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
                  advanced: Optional[bool] = False,
                  use_safearray: Optional[bool] = True):
    """ Convert COM image object into an uint16 Image.

    :param obj: COM object
    :param name: optional name for the image
    :param width: width of the image
    :param height: height of the image
    :param bit_depth: bit depth of the image
    :param advanced: advanced scripting flag
    :param use_safearray: use safearray method
    """
    from pytemscript.modules import Image

    if use_safearray:
        from comtypes.safearray import safearray_as_ndarray
        with safearray_as_ndarray:
            data = obj.AsSafeArray.astype("uint16")  # AsSafeArray always returns int32 array
    else:
        data = obj.AsSafeArray.astype("uint16")

    name = name or obj.Name

    metadata = {
        "width": width or int(obj.Width),
        "height": height or int(obj.Height),
        "bit_depth": int(bit_depth or (obj.BitDepth if advanced else obj.Depth)),
        "pixel_type": ImagePixelType(obj.PixelType).name if advanced else ImagePixelType.SIGNED_INT.name,
    }

    if advanced:
        metadata.update({item.Key: item.ValueAsString for item in obj.Metadata})
    if "BitsPerPixel" in metadata:
        metadata["bit_depth"] = int(metadata["BitsPerPixel"])

    return Image(data, name, metadata)


class RequestBody:
    """ Dataclass-like structure of a request passed to the client. """
    def __init__(self,
                 attr: str = "",
                 validator: Optional[Any] = None,
                 **kwargs) -> None:
        self.attr = attr
        self.validator = validator
        self.kwargs = kwargs

    def __str__(self) -> str:
        return '{"attr": "%s", "validator": "%s", "kwargs": %s}' % (
            self.attr, self.validator, self.kwargs)

    def __repr__(self) -> str:
        return 'RequestBody(attr=%s, validator=%s, kwargs=%s)' % (
            self.attr, self.validator, self.kwargs)
