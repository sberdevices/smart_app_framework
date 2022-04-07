# coding: utf-8
import unittest

from smart_kit.models import dialogue_manager
from smart_kit.utils.picklable_mock import PicklableMock


class TestScenarioDesc(dict):
    def get_keys(self):
        return self.keys()


async def mock_two_parameters_return_false(x, y):
    return False


async def mock_scenario1_text_fits():
    return False


async def mock_scenario2_text_fits():
    return True


async def mock_scenario1_run(x, y):
    return x.name + y.name


async def mock_scenario2_run(x, y):
    return y.name + x.name


class ModelsTest1(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_user1 = PicklableMock()
        self.test_user1.name = "TestName"
        self.test_user1.last_scenarios = PicklableMock()
        self.test_user1.last_scenarios.scenarios_names = []
        self.test_user1.message.payload = {"skillId": 1, "intent": 2}
        self.test_user1.descriptions = {'external_actions': {}}
        self.test_user2 = PicklableMock()
        self.test_user2.name = "TestName"
        self.test_user2.last_scenarios = PicklableMock()
        self.test_user2.last_scenarios.scenarios_names = [1, 2]
        self.test_user2.message.payload = {"skillId": 1, "intent": 2}
        self.test_user2.descriptions = {'external_actions': {}}
        self.test_user3 = PicklableMock()
        self.test_user3.name = "TestName"
        self.test_user3.last_scenarios = PicklableMock()
        self.test_user3.last_scenarios.scenarios_names = [1]
        self.test_user3.message.payload = {"skillId": 1, "intent": 2}
        self.test_user3.descriptions = {'external_actions': {}}
        self.test_user4 = PicklableMock()
        self.test_user4.name = "TestName"
        self.test_user4.last_scenarios = PicklableMock()
        self.test_user4.last_scenarios.scenarios_names = []
        self.test_user4.message.payload = {"skillId": 1, "intent": 2}
        self.test_user4.descriptions = {'external_actions': {'before_action': PicklableMock()}}
        self.test_text_preprocessing_result = PicklableMock()
        self.test_text_preprocessing_result.name = "Result"
        self.test_scenario1 = PicklableMock()
        self.test_scenario1.scenario_description = "This is test scenario 1 desc"
        self.test_scenario1.text_fits = mock_scenario1_text_fits
        self.test_scenario1.text_fits = mock_two_parameters_return_false
        self.test_scenario1.run = mock_scenario1_run
        self.test_scenario2 = PicklableMock()
        self.test_scenario2.scenario_description = "This is test scenario 2 desc"
        self.test_scenario2.text_fits = mock_scenario2_text_fits
        self.test_scenario2.run = mock_scenario2_run
        self.test_scenarios = TestScenarioDesc({1: self.test_scenario1, 2: self.test_scenario2})
        self.TestAction = PicklableMock()
        self.TestAction.description = "test_function"
        self.TestAction.run = mock_scenario1_run
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

    async def test_dialogue_manager_run(self):
        obj1 = dialogue_manager.DialogueManager({'scenarios': self.test_scenarios,
                                                'external_actions': {'nothing_found_action': self.TestAction}},
                                                self.app_name)
        obj2 = dialogue_manager.DialogueManager({'scenarios': self.test_scenarios,
                                                 'external_actions': {}}, self.app_name)

        # путь по умолчанию без выполнения условий
        self.assertTrue(
            await obj1.run(self.test_text_preprocessing_result, self.test_user1) == ("TestNameResult", True)
        )
        self.assertTrue(
            await obj2.run(self.test_text_preprocessing_result, self.test_user1) == ("TestNameResult", True)
        )

        # случай когда срабатоли оба условия
        self.assertTrue(
            await obj1.run(self.test_text_preprocessing_result, self.test_user2) == ("TestNameResult", True)
        )
        # случай, когда 2-е условие не выполнено
        self.assertTrue(
            await obj2.run(self.test_text_preprocessing_result, self.test_user3) == ('TestNameResult', True)
        )

    async def test_dialogue_manager_run_scenario(self):
        obj = dialogue_manager.DialogueManager({'scenarios': self.test_scenarios,
                                                'external_actions': {'nothing_found_action': self.TestAction}},
                                               self.app_name)
        self.assertTrue(
            await obj.run_scenario(1, self.test_text_preprocessing_result, self.test_user1) == "ResultTestName"
        )
        self.assertTrue(
            await obj.run_scenario(2, self.test_text_preprocessing_result, self.test_user1) == "TestNameResult"
        )
