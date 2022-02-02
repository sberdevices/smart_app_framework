# coding: utf-8
import json
import unittest
from unittest.mock import Mock

from smart_kit.message.smart_app_push_message import SmartAppPushToMessage


class TestSmartAppPushMessage(unittest.TestCase):
    def setUp(self):
        self.command_ = Mock()
        self.request_ = Mock()
        self.message_ = Mock()
        self.command_.loader = "json.dumps"
        self.request_.header = "json"
        self.command_.payload = {
            "content": {"test_param": ""},
            "surface": "some_surface",
            "project_id": "project_id",
        }
        self.message_.sub = 'sub'

    def test_smart_app_push_message_as_dict(self):
        obj = SmartAppPushToMessage(self.command_, self.message_, self.request_)
        self.assertEqual(obj.as_dict, {
            "content": {"test_param": ""},
            "surface": "some_surface",
            "clientId": "sub",
            "projectId": "project_id"
        })

    def test_smart_app_push_message_value(self):
        obj = SmartAppPushToMessage(self.command_, self.message_, self.request_)
        self.assertEqual(obj.value, json.dumps({
            "projectId": "project_id",
            "clientId": "sub",
            "surface": "some_surface",
            "content": {"test_param": ""},
        }, ensure_ascii=False))
