from core.descriptions.descriptions_items import DescriptionsItems
from core.request.base_request import request_factory


class ExternalRequests(DescriptionsItems):
    def __init__(self, items):
        super(ExternalRequests, self).__init__(request_factory, items)
