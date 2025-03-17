from functools import lru_cache

from ..utils.misc import RequestBody


class BasicClient:
    """ The methods below must be implemented in the subclasses. """
    @property
    @lru_cache(maxsize=1)
    def has_advanced_iface(self) -> bool:
        raise NotImplementedError("Method must be implemented in subclass")

    @property
    @lru_cache(maxsize=1)
    def has_lowdose_iface(self) -> bool:
        raise NotImplementedError("Method must be implemented in subclass")

    @property
    @lru_cache(maxsize=1)
    def has_ccd_iface(self) -> bool:
        raise NotImplementedError("Method must be implemented in subclass")

    @property
    @lru_cache(maxsize=1)
    def has_calgetter_iface(self) -> bool:
        raise NotImplementedError("Method must be implemented in subclass")

    def call(self, method: str, body: RequestBody):
        """ Main method used by modules. """
        raise NotImplementedError("Method must be implemented in subclass")

    def disconnect(self):
        """ Disconnect the client. """
        raise NotImplementedError("Method must be implemented in subclass")
