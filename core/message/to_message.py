# coding=utf-8

import json
from lazy import lazy


class ToMessage:
    def __init__(self, commands, message, request, fields_to_copy_from_payload=None):
        self.commands = commands
        self.incoming_message = message
        self.incremental_id = message.incremental_id
        self.uuid = message.uuid
        self.fields_to_copy_from_payload = fields_to_copy_from_payload or {}
        self.update_payloads_with_incoming_payload(commands, self.incoming_message)
        self.request = request

    def update_payloads_with_incoming_payload(self, commands, message):
        fields_to_copy_from_payload_for_channel = self.fields_to_copy_from_payload.get(message.channel, {})
        fields_to_copy = fields_to_copy_from_payload_for_channel.get("include_fields", {})
        for_command_names = fields_to_copy_from_payload_for_channel.get("for_command_names", {})
        if fields_to_copy and for_command_names:
            for cmd in commands:
                for msg_key, msg_value in message.payload.items():
                    if (cmd.name in for_command_names) and (msg_key in fields_to_copy) and (msg_key not in cmd.payload):
                        cmd.payload[msg_key] = msg_value

    @lazy
    def value(self):
        return json.dumps(self.as_dict, ensure_ascii=False)

    @lazy
    def messages(self):
        commands_raw = [command.raw for command in self.commands]
        return commands_raw

    @lazy
    def as_dict(self):
        return {
            "messageId": self.incremental_id,
            "uuid": self.uuid,
            "ai_version": "",
            "messages": self.messages
        }
