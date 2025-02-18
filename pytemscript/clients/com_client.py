import threading
import logging
import platform
import sys
import atexit
import comtypes
import comtypes.client
from functools import lru_cache

from ..modules.extras import Vector
from ..utils.misc import rgetattr, rsetattr, setup_logging, RequestBody
from ..utils.constants import *
from ..utils.enums import TEMScriptingError


com_module = comtypes

class COMBase:
    """ Base class that handles COM interface connections. """
    def __init__(self,
                 useLD: bool = False,
                 useTecnaiCCD: bool = False):
        self.tem = None
        self.tem_adv = None
        self.tem_lowdose = None
        self.tecnai_ccd = None

        if platform.system() == "Windows":
            logging.getLogger("comtypes").setLevel(logging.INFO)
            self._initialize(useLD, useTecnaiCCD)
            atexit.register(self._close)
        else:
            raise NotImplementedError("Running locally is only supported for Windows platform")

    @staticmethod
    def _createCOMObject(progId: str):
        """ Connect to a COM interface. """
        try:
            obj = comtypes.client.CreateObject(progId)
            logging.info("Connected to %s", progId)
            return obj
        except Exception as e:
            logging.info("Could not connect to %s: %s", progId, str(e))
            return None

    def _initialize(self, useLD: bool, useTecnaiCCD: bool):
        """ Wrapper to create interfaces as requested. """
        try:
            com_module.CoInitializeEx(com_module.COINIT_MULTITHREADED)
        except OSError:
            com_module.CoInitialize()

        self.tem_adv = self._createCOMObject(SCRIPTING_ADV)
        self.tem = self._createCOMObject(SCRIPTING_STD)

        if self.tem is None:  # try Tecnai instead
            self.tem = self._createCOMObject(SCRIPTING_TECNAI)

        if useLD:
            self.tem_lowdose = self._createCOMObject(SCRIPTING_LOWDOSE)
        if useTecnaiCCD:
            self.tecnai_ccd = self._createCOMObject(SCRIPTING_TECNAI_CCD)
            if self.tecnai_ccd is None:
                self.tecnai_ccd = self._createCOMObject(SCRIPTING_TECNAI_CCD2)
            import comtypes.gen.TECNAICCDLib

        if self.tem is None:
            raise RuntimeError("Failed to create COM object.")

    @staticmethod
    def handle_com_error(com_error):
        """ Try catching COM error. """
        try:
            default = TEMScriptingError.E_NOT_OK.value
            err = TEMScriptingError(int(getattr(com_error, 'hresult', default))).name
            logging.error('COM error: %s', err)
        except ValueError:
            logging.error('Exception : %s', sys.exc_info()[1])

    def _close(self):
        """ Release COM objects. """
        self.tem = None
        self.tem_adv = None
        self.tem_lowdose = None
        self.tecnai_ccd = None

        com_module.CoUninitialize()


class COMClient:
    """ Local COM client interface for the microscope.
    Creating an instance of this class will also create COM interfaces for the TEM.

    :param useLD: Connect to LowDose server on microscope PC (limited control only)
    :type useLD: bool
    :param useTecnaiCCD: Connect to TecnaiCCD plugin on microscope PC that controls Digital Micrograph (maybe faster than via TIA / std scripting)
    :type useTecnaiCCD: bool
    :param debug: Print debug messages
    :type debug: bool
    :param as_server: Use this client as a server process (only for remote clients)
    :type as_server: bool
    """
    def __init__(self,
                 useLD: bool = False,
                 useTecnaiCCD: bool = False,
                 debug: bool = False,
                 as_server: bool = False,
                 **kwargs):
        self.__lock = threading.Lock()

        if not as_server:
            setup_logging("com_client.log", debug=debug)

        # Create all COM interfaces
        self._scope = COMBase(useLD, useTecnaiCCD)

        if useTecnaiCCD and self._scope.tecnai_ccd is None:
            raise RuntimeError("Could not use Tecnai CCD plugin, please _set useTecnaiCCD=False")

        self.cache = dict()

    @property
    @lru_cache(maxsize=1)
    def has_advanced_iface(self) -> bool:
        return self._scope.tem_adv is not None

    @property
    @lru_cache(maxsize=1)
    def has_lowdose_iface(self) -> bool:
        return self._scope.tem_lowdose is not None

    @property
    @lru_cache(maxsize=1)
    def has_ccd_iface(self) -> bool:
        return self._scope.tecnai_ccd is not None

    def _get(self, attrname):
        return rgetattr(self._scope, attrname)

    def _has(self, attrname) -> bool:
        """ GET request with cache support. Should be used only for attributes
        that do not change.
        Behavior:
        - If the attribute's value is `True`, cache `True`.
        - If the attribute's value is `False`, cache `False`.
        - If the attribute's value is an object (not convertible to `bool`), cache `True`.
        - If the attribute does not exist, cache `False`.
        """
        if attrname not in self.cache:
            try:
                output = self._get(attrname)
                if isinstance(output, bool):
                    self.cache[attrname] = output
                else:
                    self.cache[attrname] = True
            except AttributeError:
                self.cache[attrname] = False

        return self.cache[attrname]

    def _exec(self, attrname, **kwargs):
        attrname = attrname.rstrip("()")
        if "arg" in kwargs:  # some methods expect non-keyword argument
            return rgetattr(self._scope, attrname, kwargs.get("arg"))

        return rgetattr(self._scope, attrname, **kwargs)

    def _exec_special(self, attrname, **kwargs):
        obj_cls = kwargs.pop("obj_cls")
        obj_method = kwargs.pop("obj_method")

        if obj_cls is None or obj_method is None:
            raise AttributeError("obj_class and obj_method must be specified")

        com_obj = rgetattr(self._scope, attrname)
        obj_instance = obj_cls(com_obj)
        method = getattr(obj_instance, obj_method)

        if method is None:
            raise AttributeError("Method %s not implemented for %s" % (obj_method, obj_cls))

        result = method(**kwargs)
        obj_instance.validate(result)

        return result

    def _set(self, attrname, value=None):
        if isinstance(value, Vector):
            value.check_limits()
            vector = rgetattr(self._scope, attrname, log=False)
            vector.X, vector.Y = value.components
            rsetattr(self._scope, attrname, vector)
        else:
            rsetattr(self._scope, attrname, value)

    def disconnect(self):
        """ Do nothing since COMClient is local. """
        pass

    def call(self, method: str, body: RequestBody):
        with self.__lock:
            try:
                response = None
                attrname = body.attr

                if method == "set":
                    self._set(attrname, **body.kwargs)
                elif method == "exec":
                    response = self._exec(attrname, **body.kwargs)
                elif method == "exec_special":
                    response = self._exec_special(attrname, **body.kwargs)
                elif method == "get":
                    response = self._get(attrname)
                elif method == "has":
                    response = self._has(attrname)
                else:
                    raise ValueError("Unknown method: %s" % method)

                if body.validator is not None:
                    try:
                        assert isinstance(response, body.validator)
                        #body.validator(response)
                    except TypeError or ValueError:
                        logging.error("Invalid type for %s: expected %s but %s (value=%s) was returned",
                                      attrname, body.validator, type(response), response)
                        raise
                return response

            except Exception as e:
                logging.error(e)
                raise e
