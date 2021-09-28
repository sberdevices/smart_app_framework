# coding: utf-8
import json
import unittest
from unittest.mock import Mock

from core.message.msg_validator import MessageValidator
from smart_kit.message.smartapp_to_message import SmartAppToMessage


class TestSmartAppToMessage(unittest.TestCase):
    def setUp(self):
        self.command_ = Mock()
        self.request_ = Mock()
        self.message_ = Mock()
        self.command_.payload = {"z": 1}
        self.command_.name = "AnyName"
        self.command_.loader = "json.dumps"
        self.request_.header = "json"
        self.message_.payload = {"q": 0}
        self.message_.incremental_id = 111
        self.message_.session_id = 11
        self.message_.uuid = '1234-5678-9012'
        self.output_json = '{"messageId": 111, "sessionId": 11, "messageName": "AnyName", "payload": {"z": 1}, ' \
                           '"uuid": "1234-5678-9012"}'

    def test_smart_app_to_message_1(self):
        obj = SmartAppToMessage(self.command_, self.message_, self.request_)
        self.assertTrue(obj.command.name == "AnyName")
        self.assertTrue(obj.incoming_message.uuid == '1234-5678-9012')
        self.assertTrue(obj.request.header == "json")
        self.assertTrue(obj.forward_fields == ())
        self.assertTrue(obj.payload == {"z": 1})
        self.assertTrue(obj.as_dict == {
            "messageId": 111,
            "sessionId": 11,
            "messageName": "AnyName",
            "payload": {"z": 1},
            "uuid": '1234-5678-9012'
        })
        self.assertTrue(obj.value == self.output_json)

    def test_smart_app_to_message_2(self):
        obj = SmartAppToMessage(self.command_, self.message_, self.request_, ["t"])
        self.assertTrue(obj.forward_fields == ["t"])
        self.assertTrue(obj.payload == {"z": 1})

    def test_smart_app_to_message_3(self):
        obj = SmartAppToMessage(self.command_, self.message_, self.request_, ["z"])
        self.assertTrue(obj.forward_fields == ["z"])
        self.assertTrue(obj.payload == {"z": 1})

    def test_smart_app_to_message_4(self):
        obj = SmartAppToMessage(self.command_, self.message_, self.request_, ["q"])
        self.assertTrue(obj.forward_fields == ["q"])
        self.assertTrue(obj.payload == {"z": 1, "q": 0})


class PieMessageValidator(MessageValidator):
    def validate(self, message_name: str, payload: dict):
        return 3.14 < payload.get("pi", 0) < 3.15


class TestSmartAppToMessageValidation(unittest.TestCase):
    def test_validation(self):
        command_ = Mock()
        request_ = Mock()
        message_ = Mock()
        command_.payload = {"pi": 3.14159265358979}
        command_.name = "AnyName"
        request_.header = "json"
        message_.payload = {"q": 0}
        message_.incremental_id = 111
        message_.session_id = 11
        message_.uuid = '1234-5678-9012'

        message = SmartAppToMessage(
            command_, message_, request_,
            validators=(PieMessageValidator(),))
        self.assertTrue(message.validate())

        command_.payload["pi"] = 2.7182818284
        message = SmartAppToMessage(
            command_, message_, request_,
            validators=(PieMessageValidator(),))
        self.assertFalse(message.validate())
