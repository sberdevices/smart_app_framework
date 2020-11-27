from core.model.factory import build_factory
from core.model.registered import Registered
from core.utils.exception_handlers import exc_handler
import timeout_decorator


requests_registered = Registered()
request_factory = build_factory(requests_registered)


class BaseRequest:
    BLOCKING_TIMEOUT = 0.2
    DEFAULT_ENABLED = True

    def __init__(self, items, id=None):
        self.values = items
        self.timeout = items.get("timeout")
        self._timeout_wrap = timeout_decorator.timeout(self.timeout or self.BLOCKING_TIMEOUT)
        self._enabled = items.get("enabled", self.DEFAULT_ENABLED) if items is not None else self.DEFAULT_ENABLED

    @property
    def group_key(self):
        return None

    def check_enabled(self):
        return self._enabled

    def update_empty_items(self, items):
        pass

    @exc_handler()
    def run(self, data, params=None):
        raise NotImplementedError
