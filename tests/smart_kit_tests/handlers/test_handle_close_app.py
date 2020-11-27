# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.handlers import handle_close_app


class TestScenarioDesc(dict):
    def form_type(self):
        return 'type'


class HandlerTest6(unittest.TestCase):
    def setUp(self):
        self.test_text_preprocessing_result = Mock('text_preprocessing_result')
        self.test_user = Mock()
        self.test_user.name = "TestName"
        self.test_user.forms = Mock('forms')
        self.test_user.forms.remove_item = lambda x: 20
        self.test_user.descriptions = {"scenarios": {"any scenario": TestScenarioDesc()}}
        self.test_user.last_scenarios = Mock('last_scenarios')
        self.test_user.last_scenarios.last_scenario_name = "any scenario"
        self.test_user.last_scenarios.delete = lambda x: 10
        self.test_user.message.payload = {"skillId": 1, "intent": 2}
        self.test_user.message.message_name = "TestMessageName"
        self.test_user.message.device = Mock()
        self.test_user.message.device.surface = "test_surface"
        self.test_user.message.channel = "test_channel"

        self.test_payload = {'message': {1: 1}}
        self.test_text_preprocessing_result.raw = 'any raw'
        self.app_name = "test_app"

    def test_handler_close_app_init(self):
        obj = handle_close_app.HandlerCloseApp(app_name=self.app_name)
        self.assertIsNotNone(obj.KAFKA_KEY)
        self.assertIsNotNone(obj._clear_current_scenario)

    def test_handler_close_app_run(self):
        self.assertIsNotNone(handle_close_app.log_const.KEY_NAME)
        obj = handle_close_app.HandlerCloseApp(app_name=self.app_name)
        self.assertIsNone(obj.run(self.test_payload, self.test_user))
