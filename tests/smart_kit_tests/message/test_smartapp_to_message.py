# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.message import smartapp_to_message


class MessageSmartAppToMessageTest1(unittest.TestCase):
    def setUp(self):
        self.command_ = Mock()
        self.request_ = Mock()
        self.message_ = Mock()
        self.command_.payload = {"z": 1}
        self.command_.name = "AnyName"
        self.request_.header = "json"
        self.message_.payload = {"q": 0}
        self.message_.incremental_id = 111
        self.message_.session_id = 11
        self.message_.uuid = '1234-5678-9012'
        self.output_json = '{"messageId": 111, "sessionId": 11, "messageName": "AnyName", "payload": {"z": 1}, ' \
                           '"uuid": "1234-5678-9012"}'

    def test_smart_app_to_message_1(self):
        obj = smartapp_to_message.SmartAppToMessage(self.command_, self.message_, self.request_)
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
        obj = smartapp_to_message.SmartAppToMessage(self.command_, self.message_, self.request_, ["t"])
        self.assertTrue(obj.forward_fields == ["t"])
        self.assertTrue(obj.payload == {"z": 1})

    def test_smart_app_to_message_3(self):
        obj = smartapp_to_message.SmartAppToMessage(self.command_, self.message_, self.request_, ["z"])
        self.assertTrue(obj.forward_fields == ["z"])
        self.assertTrue(obj.payload == {"z": 1})

    def test_smart_app_to_message_4(self):
        obj = smartapp_to_message.SmartAppToMessage(self.command_, self.message_, self.request_, ["q"])
        self.assertTrue(obj.forward_fields == ["q"])
        self.assertTrue(obj.payload == {"z": 1, "q": 0})
