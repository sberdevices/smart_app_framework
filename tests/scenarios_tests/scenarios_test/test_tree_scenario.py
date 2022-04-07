from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, MagicMock, AsyncMock

from core.basic_models.actions.basic_actions import Action, action_factory, actions
from core.basic_models.actions.command import Command
from core.model.registered import registered_factories
from scenarios.scenario_descriptions.tree_scenario.tree_scenario import TreeScenario
from smart_kit.utils.picklable_mock import PicklableMock, PicklableMagicMock, AsyncPicklableMock


class MockAction:
    def __init__(self, items=None, command_name=None):
        self.called = False
        self.command_name = command_name

    async def run(self, user, text_preprocessing_result, params):
        self.called = True
        if self.command_name:
            return [Command(self.command_name)]


class BreakAction:
    def __init__(self, items=None):
        pass

    async def run(self, user, text_preprocessing_result, params):
        user.scenario_models["some_id"].break_scenario = True
        return []


class TestTreeScenario(IsolatedAsyncioTestCase):

    async def test_1(self):
        """
        Тест проверяет сценарий из одного узла. Предполагается идеальный случай, когда одно поле
        и мы смогли его заполнить.
        Тест очень сложен с точки зрения инициализации моков. Но это лучше чем усложнять в целом процесс тестирования,
        используя полноценные сущности.
        """

        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        actions["external"] = MockAction

        form_type = "form for doing smth"
        internal_form_key = "my form key"

        node_mock = {"form_key": internal_form_key, "actions": [{"type": "test", "command": "jump", "nodes": {}}]}

        items = {"channels": "web", "form": form_type, "start_node_key": "node_1",
                 "scenario_nodes": {"node_1": node_mock}}

        field_descriptor = PicklableMock(name="field_descriptor_mock")
        field_descriptor.filler.run = AsyncMock(name="my_field_value_1", return_value=61)
        field_descriptor.fill_other = False
        field_descriptor.field_validator.actions = []
        field_descriptor.field_validator.requirement.check = AsyncMock(return_value=True)

        internal_form = PicklableMock(name="internal_form_mock")
        internal_form.description.fields.items = PicklableMock(return_value=[("age", field_descriptor)])
        internal_form.field.field_validator.requirement.check = AsyncPicklableMock(return_value=True)
        internal_form.fields = PicklableMagicMock()
        internal_form.fields.values.items = PicklableMock(return_value={"age": 61})
        internal_form.is_valid = PicklableMock(return_value=True)

        start_form_mock = PicklableMagicMock(name="start_form_mock")

        composite_form = PicklableMagicMock(name="form_mock")
        composite_form.forms = start_form_mock
        composite_form.set_valid = PicklableMock()

        context_forms = PicklableMagicMock(name="context_form_mock")
        context_forms.new = PicklableMock(return_value=PicklableMock(forms={"my form key": internal_form},
                                                                     is_endless=PicklableMock(return_value=False)))

        current_node_mock = PicklableMock(name="current_node_mock")
        current_node_mock.form_key = "start_node_mock"
        current_node_mock.available_nodes = False

        user = PicklableMock()
        user.forms = context_forms
        user.scenario_models = PicklableMagicMock()
        user.scenario_models.__getitem__ = PicklableMock(name="scenario_mock", return_value=current_node_mock)

        text_preprocessing_result = None

        scenario = TreeScenario(items, 1)

        await scenario.run(text_preprocessing_result, user)
        self.assertIsNone(current_node_mock.current_node)
        context_forms.new.assert_called_once_with(form_type)

    async def test_break(self):
        """
        Тест проверяет выход из сценария если сработает флаг break_scenario
        """

        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        actions["break"] = MockAction
        actions["success"] = MockAction
        actions["external"] = MockAction

        form_type = "form for doing smth"
        internal_form_key = "my form key"

        node_mock = {"form_key": internal_form_key, "actions": [{"type": "test", "command": "jump", "nodes": {}}]}

        items = {"channels": "web", "form": form_type, "start_node_key": "node_1",
                 "scenario_nodes": {"node_1": node_mock}, "actions": [{"type": "success"}]}

        field_descriptor = PicklableMock(name="field_descriptor_mock")
        field_descriptor.filler.run = AsyncMock(name="my_field_value_1", return_value=61)
        field_descriptor.fill_other = False
        field_descriptor.field_validator.actions = []
        field_descriptor.field_validator.requirement.check = AsyncMock(return_value=True)
        field_descriptor.on_filled_actions = [BreakAction(), MockAction(command_name="break action result")]
        field_descriptor.id = "age"

        internal_form = PicklableMock(name="internal_form_mock")
        internal_form.description.fields.items = PicklableMock(return_value=[("age", field_descriptor)])
        internal_form.field.field_validator.requirement.check = AsyncPicklableMock(return_value=True)
        field = PicklableMock()
        field.description = field_descriptor
        field.value = 61
        internal_form.fields = {field_descriptor: field, "age": field}
        internal_form.is_valid = PicklableMock(return_value=True)

        start_form_mock = PicklableMagicMock(name="start_form_mock")

        composite_form = PicklableMagicMock(name="form_mock")
        composite_form.forms = start_form_mock
        composite_form.set_valid = PicklableMock()

        context_forms = PicklableMagicMock(name="context_form_mock")
        context_forms.new = PicklableMock(return_value=PicklableMock(forms={"my form key": internal_form},
                                                                     is_endless=PicklableMock(return_value=False)))

        current_node_mock = PicklableMock(name="current_node_mock")
        current_node_mock.form_key = "start_node_mock"
        current_node_mock.available_nodes = False

        user = PicklableMock()
        user.forms = context_forms
        user.scenario_models = PicklableMagicMock()
        user.scenario_models.__getitem__ = PicklableMock(name="scenario_mock", return_value=current_node_mock)

        text_preprocessing_result = None

        scenario = TreeScenario(items, 1)

        result = await scenario.run(text_preprocessing_result, user)

        self.assertFalse(scenario.actions[0].called)
        self.assertEqual(result[0].name, "break action result")
