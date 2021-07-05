import collections
import copy
import json
import time

from lazy import lazy
from jinja2 import exceptions as jexcept
from typing import Optional, Dict, Any, Union, List

from core.basic_models.actions.basic_actions import Action
from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.basic_models.parametrizers.parametrizer import BasicParametrizer
from core.basic_models.requirement.basic_requirements import Requirement
from core.configs.global_constants import CALLBACK_ID_HEADER
from core.logging.logger_utils import log
from core.model.factory import factory, list_factory
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate
from core.utils.pickle_copy import pickle_deepcopy

import scenarios.logging.logger_constants as log_const
from scenarios.actions.action_params_names import TO_MESSAGE_NAME, TO_MESSAGE_PARAMS, SAVED_MESSAGES, \
    REQUEST_FIELD, LOCAL_VARS
from scenarios.user.parametrizer import Parametrizer
from scenarios.user.user_model import User
from scenarios.scenario_models.history import Event
from smart_kit.names.action_params_names import SEND_TIMESTAMP


class ClearFormAction(Action):
    version: Optional[int]
    parametrizer: BasicParametrizer
    form: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(ClearFormAction, self).__init__(items, id)
        self.form = items["form"]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        user.forms.remove_item(self.form)


class ClearInnerFormAction(ClearFormAction):
    version: Optional[int]
    parametrizer: BasicParametrizer
    form: str
    inner_form: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(ClearInnerFormAction, self).__init__(items, id)
        self.inner_form = items["inner_form"]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        form = user.forms[self.form]
        if form:
            form.forms.remove_item(self.inner_form)


class RemoveFormFieldAction(Action):
    version: Optional[int]
    parametrizer: BasicParametrizer
    form: str
    field: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(RemoveFormFieldAction, self).__init__(items, id)
        self.form = items["form"]
        self.field = items["field"]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        form = user.forms[self.form]
        form.fields.remove_item(self.field)


class RemoveCompositeFormFieldAction(RemoveFormFieldAction):
    version: Optional[int]
    parametrizer: BasicParametrizer
    form: str
    field: str
    inner_form: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(RemoveCompositeFormFieldAction, self).__init__(items, id)
        self.inner_form = items["inner_form"]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        form = user.forms[self.form]
        inner_form = form.forms[self.inner_form]
        inner_form.fields.remove_item(self.field)


class BreakScenarioAction(Action):
    scenario_id: Optional[str]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(BreakScenarioAction, self).__init__(items, id)
        self.scenario_id = items.get("scenario_id")

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        scenario_id = self.scenario_id if self.scenario_id is not None else user.last_scenarios.last_scenario_name
        user.scenario_models[scenario_id].set_break()


class AskAgainAction(Action):

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        last_scenario_id = user.last_scenarios.last_scenario_name
        scenario = user.descriptions["scenarios"].get(last_scenario_id)
        return scenario.get_ask_again_question_result(text_preprocessing_result, user, params)


class SaveBehaviorAction(Action):
    version: Optional[int]
    parametrizer: BasicParametrizer
    behavior: str
    check_scenario: bool

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(SaveBehaviorAction, self).__init__(items, id)
        self.behavior = items["behavior"]
        self.check_scenario = items.get("check_scenario", True)

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        scenario_id = None
        if self.check_scenario:
            scenario_id = user.last_scenarios.last_scenario_name
        user.behaviors.add(user.message.generate_new_callback_id(), self.behavior, scenario_id,
                           text_preprocessing_result.raw, action_params=pickle_deepcopy(params))


class BasicSelfServiceActionWithState(StringAction):
    version: Optional[int]
    parametrizer: BasicParametrizer
    behavior: str
    command_action: Action

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        self.behavior = items["behavior"]
        self._command_action: Dict[str, Any] = items["command_action"]
        self._check_scenario: bool = items.get("check_scenario", True)
        super(BasicSelfServiceActionWithState, self).__init__(self._command_action, id)

    @lazy
    def behavior_action(self) -> SaveBehaviorAction:
        return SaveBehaviorAction({"behavior": self.behavior, "check_scenario": self._check_scenario})

    @lazy
    def command_action(self) -> StringAction:
        return StringAction(self._command_action)

    def _check(self, user):
        return not user.behaviors.check_got_saved_id(self.behavior_action.behavior)

    def _run(self, user, text_preprocessing_result, params=None):
        self.behavior_action.run(user, text_preprocessing_result, params)
        command_action_result = self.command_action.run(user, text_preprocessing_result, params) or []
        return command_action_result

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Union[None, str, List[Command]]:
        if self._check(user):
            return self._run(user, text_preprocessing_result, params)


class BaseSetVariableAction(Action):
    key: str
    loader: Optional[str]
    loaders = collections.defaultdict(str, {"json": json.loads, "float": float, "int": int})
    value: Union[str, Dict]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(BaseSetVariableAction, self).__init__(items, id)
        self.key: str = items["key"]
        self.loader = items.get('loader')
        value: str = items["value"]
        self.template: UnifiedTemplate = UnifiedTemplate(value)

    def _set(self, user, value):
        raise NotImplemented

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        params = user.parametrizer.collect(text_preprocessing_result)
        try:
            # if path is wrong, it may fail with UndefinedError
            # notion: {key: None} will return "None";
            # not existing key or value "" will return ""; otherwise question in scenario will go in cycles
            value = self.template.render(params)
        except jexcept.UndefinedError:
            value = None

        if self.loader:
            if value:
                loader = self.loaders[self.loader]
                value = loader(value)
            else:
                value = None

        self._set(user, value)


class SetVariableAction(BaseSetVariableAction):
    version: Optional[int]
    parametrizer: BasicParametrizer
    loader: Optional[str]
    key: str
    loaders = collections.defaultdict(str, {"json": json.loads, "float": float, "int": int})
    ttl: int
    value: Union[str, Dict]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(SetVariableAction, self).__init__(items, id)
        self.ttl: int = items.get("ttl")

    def _set(self, user, value):
        user.variables.set(self.key, value, self.ttl)


class DeleteVariableAction(Action):
    version: Optional[int]
    key: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(DeleteVariableAction, self).__init__(items, id)
        self.key: str = items["key"]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        user.variables.delete(self.key)


class ClearVariablesAction(Action):
    version: Optional[int]

    def __init__(self, items: Dict[str, Any] = None, id: Optional[str] = None):
        super(ClearVariablesAction, self).__init__(items, id)

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        user.variables.clear()


class FillFieldAction(Action):
    version: Optional[int]
    parametrizer: BasicParametrizer
    form: str
    field: str
    data_path: Union[str, Dict[str, Any]]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(FillFieldAction, self).__init__(items, id)
        self.form = items["form"]
        self.field: str = items["field"]
        data_path = items["data_path"]
        self.template: UnifiedTemplate = UnifiedTemplate(data_path)

    def _fill(self, user, data):
        if data is not None:
            user.forms[self.form].fields[self.field].set_available()
            user.forms[self.form].fields[self.field].fill(data)

    def _get_data(self, params):
        return self.template.render(params)

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        params = user.parametrizer.collect(text_preprocessing_result)
        data = self._get_data(params)
        self._fill(user, data)


class CompositeFillFieldAction(FillFieldAction):
    version: Optional[int]
    parametrizer: BasicParametrizer
    internal_form: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(CompositeFillFieldAction, self).__init__(items, id)
        self.internal_form = items["internal_form"]

    def _fill(self, user, data):
        if data is not None:
            user.forms[self.form].forms[self.internal_form].fields[self.field].set_available()
            user.forms[self.form].forms[self.internal_form].fields[self.field].fill(data)


class RunScenarioAction(Action):
    version: Optional[int]
    parametrizer: BasicParametrizer

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(RunScenarioAction, self).__init__(items, id)
        self.scenario: UnifiedTemplate = UnifiedTemplate(items["scenario"])

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Union[None, str, List[Command]]:
        if params is None:
            params = user.parametrizer.collect(text_preprocessing_result)
        else:
            params.update(user.parametrizer.collect(text_preprocessing_result))
        scenario_id = self.scenario.render(params)
        scenario = user.descriptions["scenarios"].get(scenario_id)
        if scenario:
            return scenario.run(text_preprocessing_result, user, params)


class RunLastScenarioAction(Action):
    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Union[None, str, List[Command]]:
        last_scenario_id = user.last_scenarios.last_scenario_name
        scenario = user.descriptions["scenarios"].get(last_scenario_id)
        if scenario:
            return scenario.run(text_preprocessing_result, user, params)


class ChoiceScenarioAction(Action):
    FIELD_SCENARIOS_KEY = "scenarios"
    FIELD_ELSE_KEY = "else_action"
    FIELD_REQUIREMENT_KEY = "requirement"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(ChoiceScenarioAction, self).__init__(items, id)
        self._else_item = items.get(self.FIELD_ELSE_KEY)
        self._scenarios = items[self.FIELD_SCENARIOS_KEY]
        self._requirements = [scenario.pop(self.FIELD_REQUIREMENT_KEY) for scenario in self._scenarios]

        self.requirement_items = self.build_requirement_items()

        if self._else_item:
            self.else_item = self.build_else_item()
        else:
            self.else_item = None

    @list_factory(Requirement)
    def build_requirement_items(self):
        return self._requirements

    @factory(Action)
    def build_else_item(self):
        return self._else_item

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Union[None, str, List[Command]]:
        result = None
        choice_is_made = False

        for scenario, requirement in zip(self._scenarios, self.requirement_items):
            check_res = requirement.check(text_preprocessing_result, user, params)
            if check_res:
                result = RunScenarioAction(items=scenario).run(user, text_preprocessing_result, params)
                choice_is_made = True
                break

        if not choice_is_made and self._else_item:
            result = self.else_item.run(user, text_preprocessing_result, params)

        return result


class ClearCurrentScenarioAction(Action):

    def _clear_scenario(self, user, scenario_id):
        scenario = user.descriptions["scenarios"][scenario_id]
        user.last_scenarios.delete(scenario_id)
        user.forms.remove_item(scenario.form_type)

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        last_scenario_id = user.last_scenarios.last_scenario_name
        if last_scenario_id:
            self._clear_scenario(user, last_scenario_id)


class ClearScenarioByIdAction(ClearCurrentScenarioAction):
    version: Optional[int]
    parametrizer: BasicParametrizer
    scenario_id: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(ClearScenarioByIdAction, self).__init__(items, id)
        self.scenario_id = items.get("scenario_id")

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        if self.scenario_id:
            self._clear_scenario(user, self.scenario_id)


class ClearCurrentScenarioFormAction(Action):
    def __init__(self, items, id=None):
        super().__init__(items, id)

    def run(self, user, text_preprocessing_result, params=None):
        last_scenario_id = user.last_scenarios.last_scenario_name
        if last_scenario_id:
            user.forms.clear_form(last_scenario_id)


class ResetCurrentNodeAction(Action):
    def __init__(self, items, id=None):
        super().__init__(items, id)
        self.node_id = items.get('node_id', None)

    def run(self, user, text_preprocessing_result, params=None):
        last_scenario_id = user.last_scenarios.last_scenario_name
        if last_scenario_id:
            user.scenario_models[last_scenario_id].current_node = self.node_id


class AddHistoryEventAction(Action):
    results: UnifiedTemplate
    event_type: UnifiedTemplate
    event_content: Dict[str, UnifiedTemplate]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(AddHistoryEventAction, self).__init__(items, id)
        self.results = UnifiedTemplate(items.get("results"))
        self.event_type = UnifiedTemplate(items.get("event_type"))
        self.event_content = items.get("event_content")
        if self.event_content:
            for k, v in self.event_content.items():
                self.event_content[k] = UnifiedTemplate(v)

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        last_scenario_id = user.last_scenarios.last_scenario_name
        scenario = user.descriptions["scenarios"].get(last_scenario_id)
        if scenario:

            params = user.parametrizer.collect(text_preprocessing_result)

            if self.event_content:
                for key, template in self.event_content.items():
                    self.event_content[key] = template.render(params)
            self.event_type = self.event_type.render(params)
            self.results = self.results.render(params)

            event = Event(
                type=self.event_type,
                scenario=scenario.id,
                scenario_version=scenario.version,
                results=self.results,
                content=self.event_content
            )
            user.history.add_event(event)


class EmptyAction(Action):
    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        log("%(class_name)s.run: action do nothing.",
            params={log_const.KEY_NAME: "empty_action", "class_name": self.__class__.__name__}, user=user)
        return None


class RunScenarioByProjectNameAction(Action):

    def run(self, user: User, text_preprocessing_result: TextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Union[None, str, List[Command]]:
        scenario_id = user.message.project_name
        scenario = user.descriptions["scenarios"].get(scenario_id)
        if scenario:
            return scenario.run(text_preprocessing_result, user, params)
        else:
            log("%(class_name)s warning: %(scenario_id)s isn't exist",
                params={log_const.KEY_NAME: "warning_in_RunScenarioByProjectNameAction",
                        "class_name": self.__class__.__name__, "scenario_id": scenario_id},
                user=user, level="WARNING")


class ProcessBehaviorAction(Action):
    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        callback_id = user.message.callback_id

        log("%(class_name)s.run: got callback_id %(callback_id)s.",
            params={log_const.KEY_NAME: "process_behavior_action",
                    "class_name": self.__class__.__name__,
                    "callback_id": callback_id}, user=user)

        if not user.behaviors.has_callback(callback_id):
            log("%(class_name)s.run: user.behaviors has no callback %(callback_id)s.",
                params={log_const.KEY_NAME: "process_behavior_action_warning",
                        "class_name": self.__class__.__name__,
                        "callback_id": callback_id}, level="WARNING", user=user)
            return None

        if user.message.payload:
            return user.behaviors.success(callback_id)

        return user.behaviors.fail(callback_id)


class SelfServiceActionWithState(BasicSelfServiceActionWithState):
    version: Optional[int]
    parametrizer: Parametrizer
    behavior: str
    command_action: Action

    def __init__(self, items, id=None):
        super().__init__(items, id)
        self.save_params_template_data = self._get_template_tree(items.get("save_params") or {})
        self.rewrite_saved_messages = items.get("rewrite_saved_messages", False)
        self._check_scenario: bool = items.get("check_scenario", True)

    def _run(self, user, text_preprocessing_result, params=None):

        action_params = copy.copy(params or {})

        command_params = dict()
        collected = user.parametrizer.collect(text_preprocessing_result, filter_params={"command": self.command})
        action_params.update(collected)

        scenario = None
        if self._check_scenario:
            scenario = user.last_scenarios.last_scenario_name

        for key, value in self.nodes.items():
            rendered = self._get_rendered_tree(value, action_params, self.no_empty_nodes)
            if rendered != "" or not self.no_empty_nodes:
                command_params[key] = rendered

        callback_id = user.message.generate_new_callback_id()
        request_data = copy.copy(self.request_data or {})
        request_data.update(self._get_extra_request_data(user, params, callback_id))

        save_params = self._get_save_params(user, action_params, command_params)
        self._save_behavior(callback_id, user, scenario, text_preprocessing_result, save_params)

        commands = [Command(self.command, command_params, self.id, request_type=self.request_type,
                            request_data=request_data)]
        return commands

    def _get_extra_request_data(self, user, params, callback_id):
        extra_request_data = {}
        extra_request_data[CALLBACK_ID_HEADER] = callback_id
        return extra_request_data

    def _save_behavior(self, callback_id, user, scenario, text_preprocessing_result, save_params):
        user.behaviors.add(
            callback_id,
            self.behavior,
            scenario,
            text_preprocessing_result.raw,
            save_params,
        )

    def _get_save_params(self, user, action_params, command_action_params):
        save_params = self._get_rendered_tree_recursive(self.save_params_template_data, action_params)
        save_params.update({SAVED_MESSAGES: action_params.get(SAVED_MESSAGES, {})})
        save_params.update({REQUEST_FIELD: action_params.get(REQUEST_FIELD, {})})
        save_params.update({SEND_TIMESTAMP: time.time()})

        if user.settings["template_settings"].get("self_service_with_state_save_messages", True):
            saved_messages = save_params[SAVED_MESSAGES]
            if user.message.message_name not in saved_messages or self.rewrite_saved_messages:
                saved_messages[user.message.type] = user.message.payload

        save_params.update({TO_MESSAGE_PARAMS: command_action_params})
        save_params.update({TO_MESSAGE_NAME: self.command})
        return save_params


class SetLocalVariableAction(BaseSetVariableAction):
    def _set(self, user, value):
        user.local_vars.set(self.key, value)
