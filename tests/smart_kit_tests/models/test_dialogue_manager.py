# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.models import dialogue_manager


class TestScenarioDesc(dict):
    def get_keys(self):
        return self.keys()


class ModelsTest1(unittest.TestCase):
    def setUp(self):
        self.test_user1 = Mock()
        self.test_user1.name = "TestName"
        self.test_user1.last_scenarios = Mock()
        self.test_user1.last_scenarios.scenarios_names = []
        self.test_user1.message.payload = {"skillId": 1, "intent": 2}
        self.test_user2 = Mock()
        self.test_user2.name = "TestName"
        self.test_user2.last_scenarios = Mock()
        self.test_user2.last_scenarios.scenarios_names = [1, 2]
        self.test_user2.message.payload = {"skillId": 1, "intent": 2}
        self.test_user3 = Mock()
        self.test_user3.name = "TestName"
        self.test_user3.last_scenarios = Mock()
        self.test_user3.last_scenarios.scenarios_names = [1]
        self.test_user3.message.payload = {"skillId": 1, "intent": 2}
        self.test_text_preprocessing_result = Mock()
        self.test_text_preprocessing_result.name = "Result"
        self.test_scenario1 = Mock()
        self.test_scenario1.scenario_description = "This is test scenario 1 desc"
        self.test_scenario1.text_fits = lambda x, y: False
        self.test_scenario1.run = lambda x, y: x.name + y.name
        self.test_scenario2 = Mock()
        self.test_scenario2.scenario_description = "This is test scenario 2 desc"
        self.test_scenario2.text_fits = lambda x, y: True
        self.test_scenario2.run = lambda x, y: y.name + x.name
        self.test_scenarios = TestScenarioDesc({1: self.test_scenario1, 2: self.test_scenario2})
        self.TestAction = Mock()
        self.TestAction.description = "test_function"
        self.TestAction.run = lambda x, y: x.name + y.name
        self.app_name = "test"

    def test_log_const(self):
        self.assertTrue(dialogue_manager.log_const.KEY_NAME == "key_name")
        self.assertTrue(dialogue_manager.log_const.STARTUP_VALUE == "app_startup")
        self.assertTrue(hasattr(dialogue_manager.log_const, "CHOSEN_SCENARIO_VALUE"))
        self.assertTrue(hasattr(dialogue_manager.log_const, "LAST_SCENARIO_MESSAGE"))
        self.assertTrue(not hasattr(dialogue_manager.log_const, "SCENARIO_DESCRIPTION_VAL"))

    def test_dialogue_manager_init(self):
        obj1 = dialogue_manager.DialogueManager({'scenarios': self.test_scenarios, 'external_actions': '333'},
                                                self.app_name)

        self.assertTrue(obj1.scenario_descriptions == {'scenarios': self.test_scenarios, 'external_actions': '333'})
        self.assertTrue(obj1.scenarios == self.test_scenarios)
        self.assertTrue(obj1.scenario_keys == {1, 2})
        self.assertTrue(obj1.actions == '333')
        self.assertTrue(obj1.NOTHING_FOUND_ACTION == "nothing_found_action")

    def test_dialogue_manager_found_action(self):
        obj1 = dialogue_manager.DialogueManager({'scenarios': self.test_scenarios,
                                                'external_actions': {'nothing_found_action': self.TestAction}},
                                                self.app_name)
        obj2 = dialogue_manager.DialogueManager({'scenarios': self.test_scenarios,
                                                 'external_actions': {}}, self.app_name)
        self.assertTrue(obj1._nothing_found_action().descriptions, self.TestAction.descriptions)
        with self.assertRaises(TypeError):
            obj2._nothing_found_action()

    def test_dialogue_manager_run(self):
        obj1 = dialogue_manager.DialogueManager({'scenarios': self.test_scenarios,
                                                'external_actions': {'nothing_found_action': self.TestAction}},
                                                self.app_name)
        obj2 = dialogue_manager.DialogueManager({'scenarios': self.test_scenarios,
                                                 'external_actions': {}}, self.app_name)

        # путь по умолчанию без выполнения условий
        self.assertTrue(obj1.run(self.test_text_preprocessing_result, self.test_user1) == ("TestNameResult", True))
        self.assertTrue(obj2.run(self.test_text_preprocessing_result, self.test_user1) == ("TestNameResult", True))

        # случай когда срабатоли оба условия
        self.assertTrue(obj1.run(self.test_text_preprocessing_result, self.test_user2) == ("TestNameResult", True))
        # случай, когда 2-е условие не выполнено
        self.assertTrue(obj2.run(self.test_text_preprocessing_result, self.test_user3) == ('TestNameResult', True))

    def test_dialogue_manager_run_scenario(self):
        obj = dialogue_manager.DialogueManager({'scenarios': self.test_scenarios,
                                                'external_actions': {'nothing_found_action': self.TestAction}},
                                               self.app_name)
        self.assertTrue(obj.run_scenario(1, self.test_text_preprocessing_result, self.test_user1) == "ResultTestName")
        self.assertTrue(obj.run_scenario(2, self.test_text_preprocessing_result, self.test_user1) == "TestNameResult")

