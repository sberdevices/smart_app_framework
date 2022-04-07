import unittest
from typing import Dict, Any, Union, Optional
from unittest.mock import Mock, ANY

from core.basic_models.actions.basic_actions import Action, action_factory, actions
from core.model.registered import registered_factories
from scenarios.actions.action import (
    ChoiceScenarioAction,
    ClearCurrentScenarioAction,
    ClearCurrentScenarioFormAction,
    ClearScenarioByIdAction,
    ClearVariablesAction,
    CompositeFillFieldAction,
    DeleteVariableAction,
    FillFieldAction,
    SetVariableAction,
    SelfServiceActionWithState,
    SaveBehaviorAction,
    ResetCurrentNodeAction,
    RunScenarioAction,
    RunLastScenarioAction,
    AddHistoryEventAction
)
from scenarios.actions.action import ClearFormAction, ClearInnerFormAction, BreakScenarioAction, \
    RemoveFormFieldAction, RemoveCompositeFormFieldAction
from scenarios.scenario_models.history import Event
from smart_kit.action.smart_geo_action import SmartGeoAction
from smart_kit.message.smartapp_to_message import SmartAppToMessage
from smart_kit.utils.picklable_mock import PicklableMock, PicklableMagicMock


class MockAction:
    def __init__(self, items=None):
        self.items = items or {}
        self.result = items.get("result")

    def run(self, user, text_preprocessing_result, params=None):
        return self.result or ["test action run"]


class MockParametrizer:
    def __init__(self, user, items=None):
        self.items = items or {}
        self.user = user
        self.data = items.get("data") or {}
        self.filter = items.get("filter") or False

    def collect(self, text_preprocessing_result=None, filter_params=None):
        data = {
            "person_info": self.user.person_info.raw,
            "payload": self.user.message.payload}
        data.update(self.data)
        if self.filter:
            data.update({"filter": "filter_out"})
        return data


class ClearFormIdActionTest(unittest.TestCase):
    def test_run(self):
        action = ClearFormAction({"form": "form"})
        user = PicklableMagicMock()
        action.run(user, None)
        user.forms.remove_item.assert_called_once_with("form")


class RemoveCompositeFormFieldActionTest(unittest.TestCase):
    def test_run(self):
        action = ClearInnerFormAction({"form": "form", "inner_form": "inner_form"})
        user, form = PicklableMagicMock(), PicklableMagicMock()
        user.forms.__getitem__.return_value = form
        action.run(user, None)
        form.forms.remove_item.assert_called_once_with("inner_form")


class BreakScenarioTest(unittest.TestCase):
    def test_run_1(self):
        scenario_id = "test_id"
        action = BreakScenarioAction({"scenario_id": scenario_id})
        user = PicklableMock()
        scenario_model = PicklableMagicMock()
        scenario_model.set_break = Mock(return_value=None)
        user.scenario_models = {scenario_id: scenario_model}
        action.run(user, None)
        user.scenario_models[scenario_id].set_break.assert_called_once()

    def test_run_2(self):
        scenario_id = "test_id"
        action = BreakScenarioAction({})
        user = PicklableMock()
        user.last_scenarios.last_scenario_name = "test_id"
        scenario_model = PicklableMagicMock()
        scenario_model.set_break = Mock(return_value=None)
        user.scenario_models = {scenario_id: scenario_model}
        action.run(user, None)
        user.scenario_models[scenario_id].set_break.assert_called_once()


class RemoveFormFieldActionTest(unittest.TestCase):
    def test_run(self):
        action = RemoveFormFieldAction({"form": "form", "field": "field"})
        user, form = PicklableMagicMock(), PicklableMagicMock()
        user.forms.__getitem__.return_value = form
        action.run(user, None)
        form.fields.remove_item.assert_called_once_with("field")


class RemoveCompositeFormFieldActionTest(unittest.TestCase):
    def test_run(self):
        action = RemoveCompositeFormFieldAction({"form": "form", "inner_form": "form", "field": "field"})
        user, inner_form, form = PicklableMagicMock(), PicklableMagicMock(), PicklableMagicMock()
        form.forms.__getitem__.return_value = inner_form
        user.forms.__getitem__.return_value = form
        action.run(user, None)
        inner_form.fields.remove_item.assert_called_once_with("field")


class SaveBehaviorActionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        user = PicklableMock()
        user.message = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        user.last_scenarios.last_scenario_name = "scenario_id"
        test_incremental_id = "test_incremental_id"
        user.message.incremental_id = test_incremental_id
        cls.user = user

    def test_save_behavior_scenario_name(self):
        data = {"behavior": "test"}
        behavior = PicklableMock()
        behavior.add = PicklableMock()
        self.user.behaviors = behavior
        action = SaveBehaviorAction(data)
        tpr = PicklableMock()
        tpr_raw = tpr.raw
        action.run(self.user, tpr)
        self.user.behaviors.add.assert_called_once_with(self.user.message.generate_new_callback_id(), "test",
                                                        self.user.last_scenarios.last_scenario_name, tpr_raw,
                                                        action_params=None)

    def test_save_behavior_without_scenario_name(self):
        data = {"behavior": "test", "check_scenario": False}
        behavior = PicklableMock()
        behavior.add = PicklableMock()
        self.user.behaviors = behavior
        action = SaveBehaviorAction(data)
        text_preprocessing_result_raw = PicklableMock()
        text_preprocessing_result = Mock(raw=text_preprocessing_result_raw)
        action.run(self.user, text_preprocessing_result, None)
        self.user.behaviors.add.assert_called_once_with(self.user.message.generate_new_callback_id(), "test", None,
                                                        text_preprocessing_result_raw, action_params=None)


class SelfServiceActionWithStateTest(unittest.TestCase):
    def setUp(self) -> None:
        self.user = PicklableMock()
        self.user.settings = {"template_settings": {"self_service_with_state_save_messages": True}}

    def test_action_1(self):
        data = {"behavior": "test", "check_scenario": False, "command_action": {"command": "cmd_id", "nodes": {},
                                                                                "request_data": {}}}
        registered_factories[Action] = action_factory
        actions["action_mock"] = MockAction
        self.user.parametrizer = MockParametrizer(self.user, {})
        self.user.message = PicklableMock()
        local_vars = PicklableMock()
        local_vars.values = dict()
        self.user.local_vars = local_vars
        test_incremental_id = "test_incremental_id"
        self.user.message.incremental_id = test_incremental_id
        behavior = PicklableMock()
        behavior.check_got_saved_id = Mock(return_value=False)
        self.user.behaviors = behavior
        action = SelfServiceActionWithState(data)
        text_preprocessing_result_raw = PicklableMock()
        text_preprocessing_result = Mock(raw=text_preprocessing_result_raw)
        result = action.run(self.user, text_preprocessing_result, None)
        behavior.check_got_saved_id.assert_called_once()
        behavior.add.assert_called_once()
        self.assertEqual(result[0].name, "cmd_id")
        self.assertEqual(result[0].raw, {'messageName': 'cmd_id', 'payload': {}})

    def test_action_2(self):
        data = {"behavior": "test", "check_scenario": False, "command_action": {"command": "cmd_id", "nodes": {}}}
        self.user.parametrizer = MockParametrizer(self.user, {})
        self.user.message = PicklableMock()
        test_incremental_id = "test_incremental_id"
        self.user.message.incremental_id = test_incremental_id
        behavior = PicklableMock()
        self.user.behaviors = behavior
        behavior.check_got_saved_id = Mock(return_value=True)
        action = SelfServiceActionWithState(data)
        result = action.run(self.user, None)
        behavior.add.assert_not_called()
        self.assertIsNone(result)

    def test_action_3(self):
        data = {"behavior": "test", "command_action": {"command": "cmd_id", "nodes": {}, "request_data": {}}}
        registered_factories[Action] = action_factory
        actions["action_mock"] = MockAction
        self.user.parametrizer = MockParametrizer(self.user, {})
        self.user.message = PicklableMock()
        self.user.message = PicklableMock()
        local_vars = PicklableMock()
        local_vars.values = dict()
        self.user.local_vars = local_vars
        test_incremental_id = "test_incremental_id"
        self.user.message.incremental_id = test_incremental_id
        _new_behavior_id = PicklableMock()
        self.user.message.generate_new_callback_id = lambda: _new_behavior_id
        behavior = PicklableMock()
        behavior.check_got_saved_id = Mock(return_value=False)
        behavior.add = PicklableMock()
        self.user.behaviors = behavior
        self.user.last_scenarios = PicklableMock()
        scenarios_names = ["test_scenario"]
        self.user.last_scenarios.last_scenario_name = "test_scenario"
        self.user.last_scenarios.scenarios_names = scenarios_names
        action = SelfServiceActionWithState(data)
        text_preprocessing_result_raw = PicklableMock()
        text_preprocessing_result = Mock(raw=text_preprocessing_result_raw)
        result = action.run(self.user, text_preprocessing_result, None)
        behavior.check_got_saved_id.assert_called_once()
        behavior.add.assert_called_once()
        self.assertEqual(result[0].name, "cmd_id")
        self.assertEqual(result[0].raw, {'messageName': 'cmd_id', 'payload': {}})
        behavior.add.assert_called_once_with(
            self.user.message.generate_new_callback_id(), "test", scenarios_names[-1], text_preprocessing_result_raw,
            ANY
        )


class SetVariableActionTest(unittest.TestCase):

    def setUp(self):
        template = PicklableMock()
        template.get_template = Mock(return_value=[])
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = PicklableMock()
        user.person_info = PicklableMock()
        user.descriptions = {"render_templates": template}
        user.variables = PicklableMagicMock()
        user.variables.values = {}
        user.variables.set = PicklableMock()
        self.user = user

    def test_action(self):
        action = SetVariableAction({"key": "some_key", "value": "some_value"})
        action.run(self.user, None)
        self.user.variables.set.assert_called_with("some_key", "some_value", None)

    def test_action_jinja_key_default(self):
        self.user.message.payload = {"some_value": "some_value_test"}
        action = SetVariableAction({"key": "some_key", "value": "{{payload.some_value}}"})
        action.run(self.user, None)
        self.user.variables.set.assert_called_with("some_key", "some_value_test", None)

    def test_action_jinja_no_key(self):
        self.user.message.payload = {"some_value": "some_value_test"}
        action = SetVariableAction({"key": "some_key", "value": "{{payload.no_key}}"})
        action.run(self.user, None)
        self.user.variables.set.assert_called_with("some_key", "", None)


class DeleteVariableActionTest(unittest.TestCase):

    def setUp(self):
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = PicklableMock()
        user.message.payload = {"some_value": "some_value_test"}
        user.person_info = PicklableMock()
        user.variables = PicklableMagicMock()
        user.variables.delete = PicklableMock()
        self.user = user

    def test_action(self):
        action = DeleteVariableAction({"key": "some_key_1"})
        action.run(self.user, None)
        self.user.variables.delete.assert_called_with("some_key_1")


class ClearVariablesActionTest(unittest.TestCase):

    def setUp(self):
        self.var_value = {
            "some_key_1": "some_value_1",
            "some_key_2": "some_value_2",
        }
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = PicklableMock()
        user.person_info = PicklableMock()
        user.variables = PicklableMagicMock()
        user.variables.values = self.var_value
        user.variables.clear = PicklableMock()
        self.user = user

    def test_action(self):
        action = ClearVariablesAction()
        action.run(self.user, None)
        self.user.variables.clear.assert_called_with()


class FillFieldActionTest(unittest.TestCase):

    def test_fill_field(self):
        params = {"test_field": "test_data"}
        data = {"form": "test_form", "field": "test_field", "data_path": "{{test_field}}"}
        action = FillFieldAction(data)
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {"data": params})
        user.forms = {"test_form": PicklableMock()}
        field = PicklableMock()
        field.fill = PicklableMock()
        user.forms["test_form"].fields = {"test_field": field}
        action.run(user, None)
        field.fill.assert_called_once_with(params["test_field"])


class CompositeFillFieldActionTest(unittest.TestCase):

    def test_fill_field(self):
        params = {"test_field": "test_data"}
        data = {"form": "test_form", "field": "test_field", "internal_form": "test_internal_form",
                "data_path": "{{test_field}}", "parametrizer": {"data": params}}
        action = CompositeFillFieldAction(data)
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {"data": params})
        form = PicklableMock()
        internal_form = PicklableMock()
        form.forms = {"test_internal_form": internal_form}
        user.forms = {"test_form": form}
        field = PicklableMock()
        field.fill = PicklableMock()
        user.forms["test_form"].forms["test_internal_form"].fields = {"test_field": field}
        action.run(user, None)
        field.fill.assert_called_once_with(params["test_field"])


class ScenarioActionTest(unittest.TestCase):
    def test_scenario_action(self):
        action = RunScenarioAction({"scenario": "test"})
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        scen = PicklableMock()
        scen_result = 'done'
        scen.run.return_value = scen_result
        user.descriptions = {"scenarios": {"test": scen}}
        result = action.run(user, PicklableMock())
        self.assertEqual(result, scen_result)

    def test_scenario_action_with_jinja_good(self):
        params = {'next_scenario': 'ANNA.pipeline.scenario'}
        items = {"scenario": "{{next_scenario}}"}

        action = RunScenarioAction(items)
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {"data": params})
        scen = PicklableMock()
        scen_result = 'done'
        scen.run.return_value = scen_result
        user.descriptions = {"scenarios": {"ANNA.pipeline.scenario": scen}}
        result = action.run(user, PicklableMock())
        self.assertEqual(result, scen_result)

    def test_scenario_action_no_scenario(self):
        action = RunScenarioAction({"scenario": "{{next_scenario}}"})
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        scen = PicklableMock()
        scen_result = 'done'
        scen.run.return_value = scen_result
        user.descriptions = {"scenarios": {"next_scenario": scen}}
        result = action.run(user, PicklableMock())
        self.assertEqual(result, None)

    def test_scenario_action_without_jinja(self):
        action = RunScenarioAction({"scenario": "next_scenario"})
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        scen = PicklableMock()
        scen_result = 'done'
        scen.run.return_value = scen_result
        user.descriptions = {"scenarios": {"next_scenario": scen}}
        result = action.run(user, PicklableMock())
        self.assertEqual(result, scen_result)


class RunLastScenarioActionTest(unittest.TestCase):

    def test_scenario_action(self):
        action = RunLastScenarioAction({})
        user = PicklableMock()
        scen = PicklableMock()
        scen_result = 'done'
        scen.run.return_value = scen_result
        user.descriptions = {"scenarios": {"test": scen}}
        user.last_scenarios = PicklableMock()
        last_scenario_name = "test"
        user.last_scenarios.scenarios_names = [last_scenario_name]
        user.last_scenarios.last_scenario_name = last_scenario_name
        result = action.run(user, PicklableMock())
        self.assertEqual(result, scen_result)


class ChoiceScenarioActionTest(unittest.TestCase):

    @staticmethod
    def mock_and_perform_action(test_items: Dict[str, Any], expected_result: Optional[str] = None,
                                expected_scen: Optional[str] = None) -> Union[str, None]:
        action = ChoiceScenarioAction(test_items)
        user = PicklableMock()
        user.parametrizer = MockParametrizer(user, {})
        scen = PicklableMock()
        scen.run.return_value = expected_result
        if expected_scen:
            user.descriptions = {"scenarios": {expected_scen: scen}}
        return action.run(user, PicklableMock())

    def test_choice_scenario_action(self):
        # Проверяем, что запустили нужный сценарий, в случае если выполнился его requirement
        test_items = {
            "scenarios": [
                {
                    "scenario": "test_1",
                    "requirement": {"cond": False}
                },
                {
                    "scenario": "test_2",
                    "requirement": {"cond": False}
                },
                {
                    "scenario": "test_N",
                    "requirement": {"cond": True}
                }
            ],
            "else_action": {"type": "test", "result": "ELSE ACTION IS DONE"}
        }
        expected_scen_result = "test_N_done"
        real_scen_result = self.mock_and_perform_action(
            test_items, expected_result=expected_scen_result, expected_scen="test_N")
        self.assertEqual(real_scen_result, expected_scen_result)

    def test_choice_scenario_action_no_else_action(self):
        # Проверяем, что вернули None в случае если ни один сценарий не запустился (requirement=False) и else_action нет
        test_items = {
            "scenarios": [
                {
                    "scenario": "test_1",
                    "requirement": {"cond": False}
                },
                {
                    "scenario": "test_2",
                    "requirement": {"cond": False}
                }
            ]
        }
        real_scen_result = self.mock_and_perform_action(test_items)
        self.assertIsNone(real_scen_result)

    def test_choice_scenario_action_with_else_action(self):
        # Проверяем, что выполняется else_action в случае если ни один сценарий не запустился т.к их requirement=False
        test_items = {
            "scenarios": [
                {
                    "scenario": "test_1",
                    "requirement": {"cond": False}
                },
                {
                    "scenario": "test_2",
                    "requirement": {"cond": False}
                }
            ],
            "else_action": {"type": "test", "result": "ELSE ACTION IS DONE"}
        }
        expected_scen_result = "ELSE ACTION IS DONE"
        real_scen_result = self.mock_and_perform_action(test_items, expected_result=expected_scen_result)
        self.assertEqual(real_scen_result, expected_scen_result)


class ClearCurrentScenarioActionTest(unittest.TestCase):

    def test_action(self):
        scenario_name = "test_scenario"
        user = PicklableMock()
        user.forms.remove_item = PicklableMock()

        user.last_scenarios.last_scenario_name = scenario_name
        user.last_scenarios.delete = PicklableMock()
        scenario = PicklableMock()
        scenario.form_type = scenario_name
        user.descriptions = {"scenarios": {scenario_name: scenario}}

        action = ClearCurrentScenarioAction({})
        result = action.run(user, {}, {})
        self.assertIsNone(result)
        user.last_scenarios.delete.assert_called_once()
        user.forms.remove_item.assert_called_once()

    def test_action_with_empty_scenarios_names(self):
        user = PicklableMock()
        user.forms.remove_item = PicklableMock()

        user.last_scenarios.last_scenario_name = None
        user.last_scenarios.delete = PicklableMock()

        action = ClearCurrentScenarioAction({})
        result = action.run(user, {}, {})
        self.assertIsNone(result)
        user.last_scenarios.delete.assert_not_called()
        user.forms.remove_item.assert_not_called()


class ClearScenarioByIdActionTest(unittest.TestCase):

    def test_action(self):
        scenario_name = "test_scenario"
        user = PicklableMock()
        user.forms = PicklableMock()

        user.last_scenarios.last_scenario_name = scenario_name
        scenario = PicklableMock()
        scenario.form_type = scenario_name
        user.descriptions = {"scenarios": {scenario_name: scenario}}

        action = ClearScenarioByIdAction({"scenario_id": scenario_name})
        result = action.run(user, {}, {})
        self.assertIsNone(result)
        user.last_scenarios.delete.assert_called_once()
        user.forms.remove_item.assert_called_once()

    def test_action_with_empty_scenarios_names(self):
        user = PicklableMock()
        user.forms = PicklableMock()

        user.last_scenarios.last_scenario_name = "test_scenario"

        action = ClearScenarioByIdAction({})
        result = action.run(user, {}, {})
        self.assertIsNone(result)
        user.last_scenarios.delete.assert_not_called()
        user.forms.remove_item.assert_not_called()


class ClearCurrentScenarioFormActionTest(unittest.TestCase):
    def test_action(self):
        scenario_name = "test_scenario"
        user = PicklableMock()
        user.forms = PicklableMock()
        user.forms.remove_item = PicklableMock()

        user.last_scenarios.last_scenario_name = scenario_name
        scenario = PicklableMock()
        scenario.form_type = scenario_name
        scenario.keep_forms_alive = False
        user.descriptions = {"scenarios": {scenario_name: scenario}}

        action = ClearCurrentScenarioFormAction({})
        result = action.run(user, {}, {})
        self.assertIsNone(result)
        user.forms.clear_form.assert_called_once()

    def test_action_with_empty_last_scenario(self):
        scenario_name = "test_scenario"
        user = PicklableMock()
        user.forms = PicklableMock()
        user.forms.remove_item = PicklableMock()

        user.last_scenarios.last_scenario_name = None
        scenario = PicklableMock()
        scenario.form_type = scenario_name
        scenario.keep_forms_alive = False
        user.descriptions = {"scenarios": {scenario_name: scenario}}

        action = ClearCurrentScenarioFormAction({})
        result = action.run(user, {}, {})
        self.assertIsNone(result)
        user.forms.remove_item.assert_not_called()


class ResetCurrentNodeActionTest(unittest.TestCase):
    def test_action(self):
        user = PicklableMock()
        user.forms = PicklableMock()
        user.last_scenarios.last_scenario_name = 'test_scenario'
        scenario_model = PicklableMock()
        scenario_model.current_node = 'some_node'
        user.scenario_models = {'test_scenario': scenario_model}

        action = ResetCurrentNodeAction({})
        result = action.run(user, {}, {})
        self.assertIsNone(result)
        self.assertIsNone(user.scenario_models['test_scenario'].current_node)

    def test_action_with_empty_last_scenario(self):
        user = PicklableMock()
        user.forms = PicklableMock()
        user.last_scenarios.last_scenario_name = None
        scenario_model = PicklableMock()
        scenario_model.current_node = 'some_node'
        user.scenario_models = {'test_scenario': scenario_model}

        action = ResetCurrentNodeAction({})
        result = action.run(user, {}, {})
        self.assertIsNone(result)
        self.assertEqual('some_node', user.scenario_models['test_scenario'].current_node)

    def test_specific_target(self):
        user = PicklableMock()
        user.forms = PicklableMock()
        user.last_scenarios.last_scenario_name = 'test_scenario'
        scenario_model = PicklableMock()
        scenario_model.current_node = 'some_node'
        user.scenario_models = {'test_scenario': scenario_model}

        items = {
            'node_id': 'another_node'
        }
        action = ResetCurrentNodeAction(items)
        result = action.run(user, {}, {})
        self.assertIsNone(result)
        self.assertEqual('another_node', user.scenario_models['test_scenario'].current_node)


class AddHistoryEventActionTest(unittest.TestCase):

    def setUp(self):
        main_form = PicklableMock()
        main_form.field_1 = "value_1"
        parametrizer = PicklableMock()
        message = PicklableMock()
        message.name = "CLIENT_INFO_RESPONSE"
        parametrizer.collect = Mock(return_value={"message": message, "main_form": main_form})

        self.user = Mock(parametrizer=parametrizer)
        self.user.history = PicklableMock()
        self.user.history.add_event = PicklableMock()
        self.user.last_scenarios.last_scenario_name = 'test_scenario'

    def test_action_with_non_empty_scenario(self):
        scenario = PicklableMock()
        scenario.id = 'name'
        scenario.version = '1.0'
        self.user.descriptions = {'scenarios': {'test_scenario': scenario}}
        items = {
            'event_type': 'type',
            'event_content': {'foo': 'bar'},
            'results': 'result'
        }
        expected = Event(
            type='type',
            results='result',
            content={'foo': 'bar'},
            scenario='name',
            scenario_version='1.0'
        )

        action = AddHistoryEventAction(items)
        action.run(self.user, None, None)

        self.user.history.add_event.assert_called_once()
        self.user.history.add_event.assert_called_once_with(expected)

    def test_action_with_empty_scenario(self):
        self.user.descriptions = {'scenarios': {}}
        items = {
            'event_type': 'type',
            'event_content': {'foo': 'bar'},
            'results': 'result'
        }

        action = AddHistoryEventAction(items)
        action.run(self.user, None, None)

        self.user.history.add_event.assert_not_called()

    def test_action_with_jinja(self):
        scenario = PicklableMock()
        scenario.id = 'name'
        scenario.version = '1.0'
        self.user.descriptions = {'scenarios': {'test_scenario': scenario}}
        items = {
            'event_type': 'type',
            'event_content': {'field_1': '{{ main_form.field_1 }}'},
            'results': '{{ message.name }}'
        }
        expected = Event(
            type='type',
            results='CLIENT_INFO_RESPONSE',
            content={'field_1': 'value_1'},
            scenario='name',
            scenario_version='1.0'
        )

        action = AddHistoryEventAction(items)
        action.run(self.user, None, None)

        self.user.history.add_event.assert_called_once()
        self.user.history.add_event.assert_called_once_with(expected)


class SmartGeoActionTest(unittest.TestCase):

    def setUp(self):
        items = {"type": "smart_geo"}
        self.smart_geo_action = SmartGeoAction(items)

    def test_action_send_request(self):
        incoming_message = Mock(incremental_id="1605196199186625000",
                                session_id="0062530b-5521-42cc-90b0-a9d65dea4e98",
                                uuid={"userChannel": "B2C", "userId": "ec8a9097-1508-4bec-8d97-67f2329c03e0",
                                      "sub": "385342565001000018390f1f"},
                                payload={})
        user = Mock()
        text_preprocessing_result = Mock()
        params = Mock()
        command = self.smart_geo_action.run(user, text_preprocessing_result, params)[0]
        answer = SmartAppToMessage(command, incoming_message, None)
        expected = {
            "messageId": "1605196199186625000",
            "sessionId": "0062530b-5521-42cc-90b0-a9d65dea4e98",
            "messageName": "GET_PROFILE_DATA",
            "uuid": {
                "userId": "ec8a9097-1508-4bec-8d97-67f2329c03e0",
                "userChannel": "B2C",
                "sub": "385342565001000018390f1f"
            },
            "payload": {
            }
        }
        self.assertEqual(answer.as_dict, expected)
