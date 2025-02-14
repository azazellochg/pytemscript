from typing import Optional
import functools
import logging
from logging.handlers import TimedRotatingFileHandler

from pytemscript.utils.constants import MAGIC_BYTES


def rgetattr(obj, attrname, *args, **kwargs):
    """ Recursive getattr or callable on a COM object"""
    try:
        log = kwargs.pop("log", True)
        if log:
            logging.debug("<= GET: %s, args=%s, kwargs=%s",
                          attrname, args, kwargs)
        result = functools.reduce(getattr, attrname.split('.'), obj)
        return result(*args, **kwargs) if args or kwargs else result
    except:
        logging.error("Attribute error %s", attrname)
        raise AttributeError("AttributeError: %s" % attrname)


def rsetattr(obj, attrname, value):
    """ https://stackoverflow.com/a/31174427 """
    logging.debug("=> SET: %s = %s", attrname, value)
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

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    formatter = logging.Formatter(fmt)

    file_handler = TimedRotatingFileHandler(fn, when="midnight", interval=1, backupCount=7)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)


def send_data(socket, data: bytes):
    """ Assemble data packet and send it over socket. """
    packet = bytearray()
    packet.extend(MAGIC_BYTES)
    packet.extend(len(data).to_bytes(4, byteorder="big"))
    packet.extend(data)
    socket.sendall(packet)


def receive_data(socket) -> bytes:
    """ Received a packet and extract data. """
    header = socket.recv(6)
    if len(header) != 6:
        raise ValueError("Incomplete header received")
    if header[:2] != MAGIC_BYTES:
        raise ValueError("Invalid magic bytes received")

    data_length = int.from_bytes(header[2:], 'big')

    data = bytearray()
    while len(data) < data_length:
        chunk = socket.recv(data_length - len(data))
        if not chunk:
            raise ConnectionError("Connection lost while receiving data")
        data.extend(chunk)

    return data
