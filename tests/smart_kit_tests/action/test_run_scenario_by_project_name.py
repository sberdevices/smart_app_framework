# coding: utf-8
import unittest
from unittest.mock import Mock

import scenarios.logging.logger_constants as log_const
from scenarios.actions.action import RunScenarioByProjectNameAction


class TestScenarioDesc(dict):
    def run(self, argv1, argv2, params):
        return 'result to run scenario'


class RunScenarioByProjectNameActionTest1(unittest.TestCase):
    def setUp(self):
        self.test_text_preprocessing_result = Mock('text_preprocessing_result')
        self.test_user1 = Mock('User')
        self.test_user1.name = "TestName"
        self.test_user1.message = Mock('message')
        self.test_user1.message.project_name = 'any scenario'
        self.test_user1.message.channel = 'test_channel'
        self.test_user1.descriptions = {"scenarios": {"any scenario": TestScenarioDesc([[1, 1]])}}
        self.test_user2 = Mock('User')
        self.test_user2.name = "TestName"
        self.test_user2.id = 222
        self.test_user2.message = Mock('message')
        self.test_user2.message.incremental_id = 111
        self.test_user2.message.logging_uuid = 111
        self.test_user2.message.project_name = 'specific scenario'
        self.test_user2.message.channel = 'test_channel'
        self.test_user2.descriptions = {"scenarios": {"any scenario": TestScenarioDesc()}}
        self.test_text_preprocessing_result = Mock('TextPreprocessingResult')
        self.items = {"any_key": "any value"}

    def test_run_scenario_by_project_name_run(self):
        obj1 = RunScenarioByProjectNameAction(self.items)
        # без оглядки на аннотации из PEP 484
        self.assertTrue(obj1.run(self.test_user1, self.test_text_preprocessing_result, {'any_attr': {'any_data'}}) ==
                        'result to run scenario')
        obj2 = RunScenarioByProjectNameAction(self.items)
        self.assertIsNone(obj2.run(self.test_user2, self.test_text_preprocessing_result))

    def test_run_scenario_by_project_name_log_vars(self):
        obj = RunScenarioByProjectNameAction(self.items)
        self.assertIsNotNone(log_const.KEY_NAME)
        self.assertIsNotNone(obj.__class__.__name__)
