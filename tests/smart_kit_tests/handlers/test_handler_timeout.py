# coding: utf-8
import unittest
from unittest.mock import Mock

from smart_kit.handlers import handler_timeout
from smart_kit.utils.picklable_mock import PicklableMock, PicklableMagicMock


async def mock_behaviors_timeout(x):
    return 120


class HandlerTest2(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.app_name = "TastAppName"
        self.test_user = Mock('user')
        self.test_user.id = '123-345-678'
        self.test_user.message = Mock('message')
        self.test_user.message.callback_id = 11
        self.test_user.message.incremental_id = 22
        self.test_user.message.logging_uuid = '321-654-987'
        self.test_user.message.channel = "channel"
        self.test_user.message.message_name = "test"
        self.test_user.message.app_info = None
        self.test_user.message.device = PicklableMock()
        self.test_user.message.device.surface = "surface"

        self.test_user.behaviors = Mock('behaviors')
        self.test_user.behaviors.timeout = mock_behaviors_timeout
        self.test_user.behaviors.has_callback = lambda *x, **y: PicklableMagicMock()
        self.test_user.behaviors.get_callback_action_params = lambda *x, **y: {}
        self.test_payload = Mock('payload')

    async def test_handler_timeout(self):
        obj = handler_timeout.HandlerTimeout(self.app_name)
        self.assertIsNotNone(obj.KAFKA_KEY)
        self.assertIsNotNone(handler_timeout.log_const.KEY_NAME)
        self.assertTrue(await obj.run(self.test_payload, self.test_user) == 120)
