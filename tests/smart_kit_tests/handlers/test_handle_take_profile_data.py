# coding: utf-8
import unittest
from unittest.mock import Mock, MagicMock

from smart_kit.handlers import handler_take_profile_data


class MockVariables(Mock):
    _storage = {}

    def set(self, x, y):
        self._storage[x] = y

    def __getitem__(self, item):
        return self._storage[item]

    def get(self, item, default=None):
        if item in self._storage:
            return self._storage[item]
        return default


class HandleTakeProfileDataTest(unittest.TestCase):
    def setUp(self):
        self.app_name = "TestAppName"
        self.test_payload_1 = {"server_action": {}}
        self.test_payload_2 = {"server_action": {"action_id": 1, "parameters": 1}}
        self.test_user = MagicMock('user', message=MagicMock(message_name="some_name"), variables=MockVariables())
        self.test_user.descriptions = {"external_actions": {"smart_geo_fail": MagicMock(run=lambda x, y: "fail"),
                                                            "smart_geo_success": MagicMock(run=lambda x, y: "success")}}

    def test_handle_take_profile_data_init(self):
        obj = handler_take_profile_data.HandlerTakeProfileData(self.app_name)
        self.assertIsNotNone(obj.handler_name)
        self.assertIsNotNone(handler_take_profile_data.GEO)

    def test_handle_take_profile_data_run_fail(self):
        obj = handler_take_profile_data.HandlerTakeProfileData(self.app_name)
        payload = {"status_code": {"code": 102}}
        self.assertTrue(obj.run(payload, self.test_user) == "fail")

    def test_handle_take_profile_data_run_success(self):
        obj = handler_take_profile_data.HandlerTakeProfileData(self.app_name)
        payload = {"profile_data": {"geo": {"reverseGeocoding": {"country": "Российская Федерация"},
                                            "location": {"lat": 10.125, "lon": 10.0124}}},
                   "status_code": {"code": 1}}
        self.assertTrue(obj.run(payload, self.test_user) == "success")
        self.assertEqual(self.test_user.variables.get("smart_geo"), payload["profile_data"]["geo"])
