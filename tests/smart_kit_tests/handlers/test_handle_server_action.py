# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.handlers import handle_server_action


class HandlersTest3(unittest.TestCase):
    def setUp(self):
        self.app_name = "TestAppName"
        self.test_payload_1 = {"server_action": {}}
        self.test_payload_2 = {"server_action": {"action_id": 1, "parameters": 1}}
        self.test_user = Mock('user')

    def test_handle_server_action_init(self):
        obj = handle_server_action.HandlerServerAction(self.app_name)
        self.assertTrue(obj.get_action_params(self.test_payload_1) == {})
        self.assertIsNotNone(handle_server_action.SERVER_ACTION)

    def test_handle_server_action_get_action_name(self):
        obj = handle_server_action.HandlerServerAction(self.app_name)
        with self.assertRaises(KeyError):
            obj.get_action_name(self.test_payload_1, self.test_user)
        self.assertTrue(obj.get_action_name(self.test_payload_2, self.test_user) == 1)

    def test_handle_server_action_get_action_params(self):
        obj = handle_server_action.HandlerServerAction(self.app_name)
        self.assertTrue(obj.get_action_params(self.test_payload_1) == {})
        self.assertTrue(obj.get_action_params(self.test_payload_2) == 1)
