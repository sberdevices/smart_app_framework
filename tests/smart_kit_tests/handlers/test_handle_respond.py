# coding: utf-8
import unittest
from unittest.mock import Mock, MagicMock
from smart_kit.handlers import handle_respond


class HandlerTest4(unittest.TestCase):
    def setUp(self):
        self.app_name = "TestAppName"
        self.test_user1 = Mock('user')
        self.test_user1.id = '123-345-678'  # пусть чему-то равняется
        self.test_user1.descriptions = {}
        self.test_user1.message = Mock('message')
        self.test_user1.message.callback_id = 11  # пусть чему-то равняется
        self.test_user1.message.incremental_id = 22  # пусть чему-то равняется
        self.test_user1.message.logging_uuid = '321-654-987'  # пусть чему-то равняется
        self.test_user1.message.message_name = "TestMessageName"
        self.test_user1.message.channel = "test_channel"
        self.test_user1.message.device = Mock()
        self.test_user1.message.device.surface = "test_surface"
        self.test_user1.message.app_info = {}
        self.test_user1.behaviors = MagicMock()

        self.test_action = Mock('action')
        self.test_action.run = lambda x, y, z: 10  # пусть что то возвращает
        self.test_user2 = MagicMock('user')
        self.test_user2.id = '123-345-678'  # пусть чему-то равняется
        self.test_user2.descriptions = {'external_actions': {'any action name': self.test_action}}
        self.test_user2.message = Mock('message')
        self.test_user2.message.callback_id = 11  # пусть чему-то равняется
        self.test_user2.message.incremental_id = 22  # пусть чему-то равняется
        self.test_user2.message.logging_uuid = '321-654-987'  # пусть чему-то равняется
        self.test_user2.message.message_name = "TestMessageName"
        self.test_user2.message.channel = "test_channel"
        self.test_user2.message.device = Mock()
        self.test_user2.message.device.surface = "test_surface"
        self.test_user2.message.app_info = {}
        self.callback11_action_params = MagicMock()
        self.test_user2.behaviors = Mock()
        self.test_user2.behaviors.get_callback_action_params = MagicMock(return_value=self.callback11_action_params)

        self.test_payload = {'message': {1: 1}}

    def test_handler_respond_init(self):
        obj1 = handle_respond.HandlerRespond(app_name=self.app_name)
        obj2 = handle_respond.HandlerRespond(self.app_name, "any action name")
        self.assertIsNotNone(obj1.KAFKA_KEY)
        self.assertIsNone(obj1._action_name)
        self.assertIsNotNone(obj2._action_name)

    def test_handler_respond_get_action_name(self):
        obj1 = handle_respond.HandlerRespond(app_name=self.app_name)
        obj2 = handle_respond.HandlerRespond(self.app_name, "any action name")
        self.assertIsNone(obj1.get_action_name(self.test_payload, self.test_user1))
        self.assertIsNotNone(obj2.get_action_name(self.test_payload, self.test_user1))

    def test_handler_respond_get_action_params(self):
        obj = handle_respond.HandlerRespond(app_name=self.app_name)
        self.assertTrue(obj.get_action_params(self.test_payload, self.test_user2) == self.callback11_action_params)
        self.assertTrue(obj.get_action_params("any data", self.test_user2) == self.callback11_action_params)
        self.assertTrue(obj.get_action_params(None, self.test_user2) == self.callback11_action_params)

    def test_handler_respond_run(self):
        self.assertIsNotNone(handle_respond.TextPreprocessingResult(self.test_payload.get("message", {})))
        self.assertIsNotNone(handle_respond.log_const.KEY_NAME)
        self.assertIsNotNone(handle_respond.log_const.NORMALIZED_TEXT_VALUE)
        self.assertIsNotNone(handle_respond.TextPreprocessingResult(self.test_payload.get("message", {})).raw)
        obj1 = handle_respond.HandlerRespond(app_name=self.app_name)
        obj2 = handle_respond.HandlerRespond(self.app_name, "any action name")
        with self.assertRaises(KeyError):
            obj1.run(self.test_payload, self.test_user1)
        self.assertTrue(obj2.run(self.test_payload, self.test_user2) == 10)
