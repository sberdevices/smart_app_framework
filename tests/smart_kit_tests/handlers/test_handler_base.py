# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.handlers import handler_base


class HandlersTest1(unittest.TestCase):
    def test_handler_base(self):
        self.test_user = Mock('user')
        self.test_user.message = Mock("messsage")
        self.test_user.message.message_name = "test"
        self.test_user.message.channel = "test_channel"
        self.test_user.message.device = Mock("device")
        self.test_user.message.device.surface = "test_surface"
        obj = handler_base.HandlerBase("TestAppName")
        self.assertIsNotNone(obj.TOPIC_KEY)
        self.assertIsNotNone(obj.KAFKA_KEY)
