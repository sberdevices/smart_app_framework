# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.message import app_info


class MessageAppInfoTest1(unittest.TestCase):
    def test_app_info1(self):
        obj = app_info.AppInfo(dict())
        self.assertIsNone(obj.project_id)
        self.assertIsNone(obj.application_id)
        self.assertIsNone(obj.app_version_id)
        self.assertIsNone(obj.frontend_endpoint)
        self.assertIsNone(obj.frontend_type)

    def test_app_info2(self):
        obj = app_info.AppInfo({"projectId": 1, "applicationId": 1, "appversionId": 1, "frontendEndpoint": 1,
                                "frontendType": 1})
        self.assertTrue(obj.project_id == 1)
        self.assertTrue(obj.application_id == 1)
        self.assertTrue(obj.app_version_id == 1)
        self.assertTrue(obj.frontend_endpoint == 1)
        self.assertTrue(obj.frontend_type == 1)
