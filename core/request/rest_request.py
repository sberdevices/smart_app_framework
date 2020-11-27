import requests
from timeout_decorator import timeout_decorator
from core.request.base_request import BaseRequest
from core.utils.exception_handlers import exc_handler
from core.monitoring.monitoring import monitoring


class RestNoMethodSpecifiedException(Exception):
    pass


class RestRequest(BaseRequest):
    on_exc_return = None
    BLOCKING_TIMEOUT = 0.2
    URL = "url"
    POST = "post"
    GET = "get"

    def __init__(self, items, id=None):
        super(RestRequest, self).__init__(items)
        self.url = items.get(self.URL)
        self.method = items.get("method", self.POST)
        self.rest_args = items.get("rest_args") or dict()

    @property
    def group_key(self):
        return self.URL

    @exc_handler(on_error_obj_method_name="on_timeout_error", handled_exceptions=(timeout_decorator.TimeoutError,))
    def run(self, data, params=None):
        if self.check_enabled():
            method = None
            if self.method == self.GET:
                method = self.get
            elif self.method == self.POST:
                method = self.post
            return method(data)

    def on_timeout_error(self, *args, **kwarg):
        monitoring.got_counter("core_rest_run_timeout")

    def _requests_get(self, params):
        return requests.get(self.url, params=params, **self.rest_args).text

    def _requests_post(self, data):
        return requests.post(self.url, data=data, **self.rest_args).text

    def get(self, data=None):
        return self._timeout_wrap(self._requests_get)(data)

    def post(self, data=None):
        return self._timeout_wrap(self._requests_post)(data)

    def __str__(self):
        return f"RestRequest: method={self.method} url={self.url} request_args={self.rest_args}"
