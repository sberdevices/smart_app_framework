# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.message import smartapp_to_message


class MessageSmartAppToMessageTest1(unittest.TestCase):
    def setUp(self):
        self.command_ = Mock()

    def test_smart_app_to_message_1(self):
        obj = smartapp_to_message.SmartAppToMessage(self.command_, self.message_, self.request_)
        self.assertTrue(obj.command.name == "AnyName")
        self.assertTrue(obj.incoming_message.uuid == '1234-5678-9012')
        self.assertTrue(obj.request.header == "json")
