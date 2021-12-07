from typing import Iterable
import json
from lazy import lazy
from copy import copy

from core.utils.pickle_copy import pickle_deepcopy
from core.utils.masking_message import masking
from core.message.msg_validator import MessageValidator
from smart_kit.utils import SmartAppToMessage_pb2


class SmartAppToMessage:
    ROOT_NODES_KEY = "root_nodes"
    PAYLOAD = "payload"

    def __init__(self, command, message, request, forward_fields=None, masking_fields=None,
                 validators: Iterable[MessageValidator] = ()):
        root_nodes = command.payload.pop(self.ROOT_NODES_KEY, None)
        self.command = command
        self.root_nodes = root_nodes or {}
        self.incoming_message = message
        self.request = request
        self.forward_fields = forward_fields or ()
        self.masking_fields = masking_fields
        self.validators = validators

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

    @staticmethod
    def as_protobuf_message(data_as_dict):
        message = SmartAppToMessage_pb2.SmartAppToMessage()
        message.messageId = data_as_dict["messageId"]
        message.sessionId = data_as_dict["sessionId"]
        message.messageName = data_as_dict["messageName"]
        message.payload = data_as_dict["payload"]
        uuid = message.uuid.add()
        uuid.userId = data_as_dict["uuid"]["userId"]
        uuid.userChannel = data_as_dict["uuid"]["userChannel"]
        return message

    @lazy
    def masked_value(self):
        data = pickle_deepcopy(self.as_dict)
        masking(data, self.masking_fields)
        if self.command.loader == "json.dumps":
            return json.dumps(data, ensure_ascii=False)
        elif self.command.loader == "protobuf":
            protobuf_message = self.as_protobuf_message(data)
            return protobuf_message.SerializeToString()

    @lazy
    def value(self):
        if self.command.loader == "json.dumps":
            return json.dumps(self.as_dict, ensure_ascii=False)
        elif self.command.loader == "protobuf":
            protobuf_message = self.as_protobuf_message(self.as_dict)
            return protobuf_message.SerializeToString()

    def validate(self):
        for validator in self.validators:
            if not validator.validate(self.command.name, self.payload):
                return False
        return True
