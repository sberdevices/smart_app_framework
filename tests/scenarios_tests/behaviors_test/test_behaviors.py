# coding: utf-8
import unittest
import time
from unittest.mock import Mock
from scenarios.behaviors import behaviors


class BehaviorsTest3(unittest.TestCase):
    def setUp(self):
        self.test_items1 = {"123-ASDF": {"behavior_id": 11, "expire_time": time.time() + 10, "scenario_id": 22,
                                         "text_preprocessing_result": {}, "action_params": {}}}
        self.test_items2 = {"123-ASDF": {"behavior_id": 11, "expire_time": time.time(), "scenario_id": 22,
                                         "text_preprocessing_result": {}, "action_params": {}}}
        self.test_user = Mock('User')
        self.test_user.id = 111
        self.test_user.message = Mock()
        self.test_user.message.incremental_id = 123
        self.test_user.message.logging_uuid = 222
        self.test_user.settings = Mock()
        self.test_user.settings.app_name = "test"
        self.test_descriptions = Mock('Descriptions')

    def test_behaviors_init(self):
        obj = behaviors.Behaviors(self.test_items1, self.test_descriptions, self.test_user)
        self.assertTrue(hasattr(obj, 'timeout'))
        self.assertTrue(hasattr(obj, '_delete'))
        self.assertTrue(list(obj._callbacks.keys()) == ['123-ASDF'])

    def test_behaviors_expire(self):
        obj1 = behaviors.Behaviors(self.test_items1, self.test_descriptions, self.test_user)
        obj2 = behaviors.Behaviors(self.test_items2, self.test_descriptions, self.test_user)
        source_value1 = list(obj1._callbacks.keys())
        # source_value2 = list(obj1._callbacks.keys())
        obj1.expire()
        obj2.expire()
        self.assertTrue(list(obj1._callbacks.keys()) == source_value1)
        self.assertTrue(list(obj2._callbacks.keys()) == [])

    def test_behaviors_has_callback(self):
        obj1 = behaviors.Behaviors(self.test_items1, self.test_descriptions, self.test_user)
        self.assertTrue(obj1.has_callback('123-ASDF'))

    def test_behavoirs_log_const(self):
        self.assertIsNotNone(behaviors.log_const.KEY_NAME)
        self.assertIsNotNone(behaviors.log_const.BEHAVIOR_CALLBACK_ID_VALUE)
        self.assertIsNotNone(behaviors.log_const.BEHAVIOR_DATA_VALUE)
