# coding: utf-8


class Command:
    def __init__(self, name, params=None, action_id=None, request_type=None, request_data=None):
        self.name = name
        self.payload = params or {}
        self.action_id = action_id
        self.request_type = request_type
        self.request_data = request_data or {}

    @property
    def raw(self):
        message = {"message_name": self.name, "payload": self.payload}
        if self.action_id is not None:
            message["action_id"] = self.action_id
        return message
