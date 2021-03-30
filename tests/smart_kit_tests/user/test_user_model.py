# coding: utf-8
import unittest
from unittest.mock import Mock
from scenarios.user import user_model
from core.model.field import Field


class UserTest2(unittest.TestCase):
    def setUp(self):
        self.test_scenario1 = Mock('scenario')
        self.test_scenario1.scenario_description = "This is test scenario 1 desc"
        self.test_scenario1.form_type = "any type 1"
        self.test_id = 11
        self.test_message = Mock()
        self.test_message.incremental_id = 123
        self.test_values = {11: "any val"}
        history = Mock()
        history.enabled = True
        self.test_descriptions = {"forms": {}, "last_scenarios": [11], "scenarios": [self.test_scenario1],
                                  "preprocessing_messages_for_scenario": "any msg",
                                  "preprocessing_messages_for_scenarios": "any msg", "behaviors": [],
                                  "last_action_ids": [], "history": history, "bundles": {}}
        self.test_parametrizer_cls = lambda x, y: y

    def test_smart_app_user_init(self):
        obj1 = user_model.User(self.test_id, self.test_message, None, self.test_values, self.test_descriptions,
                                       self.test_parametrizer_cls)
        obj2 = user_model.User(self.test_id, self.test_message, None, self.test_values, self.test_descriptions,
                                       self.test_parametrizer_cls, True)
        self.assertTrue(len(obj1.fields) > 0)
        self.assertTrue(obj1.id == self.test_id)
        self.assertTrue(not obj1.do_not_save)
        self.assertTrue(obj2.load_error)

    def test_smart_app_user_fields(self):
        obj1 = user_model.User(self.test_id, self.test_message, None, self.test_values, self.test_descriptions,
                                       self.test_parametrizer_cls)
        self.assertTrue(len(obj1.fields) == 13)
        self.assertTrue(isinstance(obj1.fields[0], Field))

    def test_smart_app_user_parametrizer(self):
        obj1 = user_model.User(self.test_id, self.test_message, None, self.test_values, self.test_descriptions,
                                       self.test_parametrizer_cls)
        self.assertTrue(obj1.parametrizer == {})
