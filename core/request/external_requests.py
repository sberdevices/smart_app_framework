from core.descriptions.lazy_descriptions import LazyDescriptions
from core.request.base_request import request_factory


class ExternalRequests(LazyDescriptions):
    def __init__(self, items):
        super(ExternalRequests, self).__init__(request_factory, items)
