# coding: utf-8
import unittest
from unittest.mock import Mock

from smart_kit.handlers import handler_text
from smart_kit.utils.picklable_mock import PicklableMock


async def mock_dialogue_manager1_run(x, y):
    return "TestAnswer", True


async def mock_dialogue_manager2_run(x, y):
    return "", False


class HandlerTest5(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app_name = "TestAppName"
        self.test_dialog_manager1 = Mock('dialog_manager')
        self.test_dialog_manager1.run = mock_dialogue_manager1_run
        self.test_dialog_manager2 = Mock('dialog_manager')
        self.test_dialog_manager2.run = mock_dialogue_manager2_run
        self.test_text_preprocessing_result = Mock('text_preprocessing_result')
        self.test_text_preprocessing_result.raw = 'any raw'
        self.test_user = Mock('User')
        self.test_user.id = "1234-5678-9012"
        self.test_user.message = Mock('Message')
        self.test_user.message.incremental_id = "123456"
        self.test_user.message.logging_uuid = "1234-5678"
        self.test_user.message.message_name = "test"
        self.test_user.message.device = Mock("device")
        self.test_user.message.device.surface = "test_surface"
        self.test_user.message.channel = "test_channel"
        self.test_user.message.app_info = PicklableMock()
        self.test_user.message.app_info.project_id = "1111-1111-1111-1111"
        self.test_user.message.app_info.system_name = "test"
        self.test_payload = {'message': {1: 1}}

    def test_handler_text_init(self):
        obj1 = handler_text.HandlerText(self.app_name, None)
        obj2 = handler_text.HandlerText(self.app_name, self.test_dialog_manager1)
        self.assertIsNotNone(obj1.KAFKA_KEY)
        self.assertIsNone(obj1.dialogue_manager)
        self.assertIsNotNone(obj2.dialogue_manager)
        self.assertIsNotNone(handler_text.log_const.KEY_NAME)
        self.assertIsNotNone(handler_text.log_const.STARTUP_VALUE)
        self.assertIsNotNone(obj1.__class__.__name__)

    async def test_handler_text_handle_base(self):
        obj1 = handler_text.HandlerText(self.app_name, self.test_dialog_manager1)
        obj2 = handler_text.HandlerText(self.app_name, self.test_dialog_manager2)
        self.assertTrue(await obj1._handle_base(self.test_text_preprocessing_result, self.test_user) == "TestAnswer")
        self.assertTrue(await obj2._handle_base(self.test_text_preprocessing_result, self.test_user) == [])

    async def test_handler_text_run(self):
        self.assertIsNotNone(handler_text.log_const.NORMALIZED_TEXT_VALUE)
        obj1 = handler_text.HandlerText(self.app_name, self.test_dialog_manager1)
        obj2 = handler_text.HandlerText(self.app_name, self.test_dialog_manager2)
        self.assertTrue(await obj1.run(self.test_payload, self.test_user) == "TestAnswer")
        self.assertTrue(await obj2.run(self.test_payload, self.test_user) == [])
