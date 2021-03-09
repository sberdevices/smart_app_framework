import json
from lazy import lazy
from copy import copy

from core.utils.pickle_copy import pickle_deepcopy
from core.utils.masking_message import masking


class SmartAppToMessage:
    ROOT_NODES_KEY = "root_nodes"
    PAYLOAD = "payload"

    def __init__(self, command, message, request, forward_fields=None, masking_fields=None):
        root_nodes = command.payload.pop(self.ROOT_NODES_KEY, None)
        self.command = command
        self.root_nodes = root_nodes or {}
        self.incoming_message = message
        self.request = request
        self.forward_fields = forward_fields or ()
        self.masking_fields = masking_fields

    @lazy
    def payload(self):
        payload = copy(self.command.payload)
        for field in self.forward_fields:
            if field not in self.incoming_message.payload:
                continue
            if field in payload:
                continue
            payload[field] = self.incoming_message.payload[field]
        return payload

    @lazy
    def as_dict(self):
        fields = {
            "messageId": self.incoming_message.incremental_id,
            "sessionId": self.incoming_message.session_id,
            "messageName": self.command.name,
            "payload": self.payload,
            "uuid": self.incoming_message.uuid
        }
        fields.update(self.root_nodes)
        return fields

    @lazy
    def masked_value(self):
        data = pickle_deepcopy(self.as_dict)
        masking(data, self.masking_fields)
        return json.dumps(data, ensure_ascii=False)

    @lazy
    def value(self):
        return json.dumps(self.as_dict, ensure_ascii=False)
