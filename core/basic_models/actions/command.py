# coding: utf-8


class Command:
    def __init__(self, name, params=None, action_id=None, request_type=None, request_data=None, loader=None):
        """
        Initialize Command instance with params

        :param name: str, command name
        :param params:
        :param action_id:
        :param request_type:
        :param request_data:
        :param loader: loader name for data before send. Possible loader values: json.dumps / protobuf
        """

        self.name = name
        self.payload = params or {}
        self.action_id = action_id
        self.request_type = request_type
        self.request_data = request_data or {}
        self.loader = loader or "json.dumps"

    @property
    def raw(self):
        message = {"messageName": self.name, "payload": self.payload}
        if self.action_id is not None:
            message["action_id"] = self.action_id
        return message
