# coding: utf-8
import asyncio
import random
from typing import Union, Dict, List, Any, Optional

import core.logging.logger_constants as log_const
from core.basic_models.actions.command import Command
from core.basic_models.requirement.basic_requirements import Requirement
from core.configs.global_constants import KAFKA
from core.logging.logger_utils import log
from core.model.base_user import BaseUser
from core.model.factory import build_factory, factory, list_factory
from core.model.registered import Registered
from core.text_preprocessing.base import BaseTextPreprocessingResult

actions = Registered()
action_factory = build_factory(actions)


class Action:
    version: Optional[int]
    id: Optional[str]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        items = items or {}
        self.id = id
        self.version = items.get("version", -1)

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        raise NotImplementedError

    def on_run_error(self, text_preprocessing_result, user):
        log("exc_handler: Action failed to run. Return None. MESSAGE: %(masked_message)s.", user,
            {log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE,
             "masked_message": user.message.masked_value},
            level="ERROR", exc_info=True)
        return None


class CommandAction(Action):
    DEFAULT_REQUEST_TYPE = KAFKA
    version: Optional[int]
    command: str
    request_type: Optional[str]
    request_data: Optional[Dict]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(CommandAction, self).__init__(items, id)
        items = items or {}
        self.command = items.get("command")
        self.request_type = items.get("request_type") or self.DEFAULT_REQUEST_TYPE
        self.request_data = items.get("request_data")

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        await super(CommandAction, self).run(user, text_preprocessing_result, params)
        return None


class DoingNothingAction(CommandAction):
    version: Optional[int]
    command: str
    nodes: Dict[str, str]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(DoingNothingAction, self).__init__(items, id)
        self.nodes = items.get("nodes") or {}

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = [Command(self.command, self.nodes, self.id, request_type=self.request_type,
                            request_data=self.request_data)]
        return commands


class RequirementAction(Action):
    version: Optional[int]
    requirement: Requirement
    action: Action

    FIELD_KEY = "action"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(RequirementAction, self).__init__(items, id)
        self._requirement = items["requirement"]
        # can be used not only with actions but with every entity which implements Action interface
        # to not change statics "item" key is added
        self._item = items[self.FIELD_KEY]

        self.requirement = self.build_requirement()
        self.internal_item = self.build_internal_item()

    @factory(Requirement)
    def build_requirement(self):
        return self._requirement

    @factory(Action)
    def build_internal_item(self):
        return self._item

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        result = None
        if await self.requirement.check(text_preprocessing_result, user, params):
            result = await self.internal_item.run(user, text_preprocessing_result, params)
        return result


class GatherChoiceAction(Action):
    version: Optional[int]
    requirement_actions: RequirementAction
    else_action: Action

    FIELD_REQUIREMENT_KEY = "requirement_actions"
    FIELD_ELSE_KEY = "else_action"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(GatherChoiceAction, self).__init__(items, id)
        self._requirement_items = items[self.FIELD_REQUIREMENT_KEY]
        self._else_item = items.get(self.FIELD_ELSE_KEY)

        self.items = self.build_items()

        if self._else_item:
            self.else_item = self.build_else_item()
        else:
            self.else_item = None

    @list_factory(RequirementAction)
    def build_items(self):
        return self._requirement_items

    @factory(Action)
    def build_else_item(self):
        return self._else_item

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        result = None
        choice_is_made = False
        check_results = await asyncio.gather(
            item.requirement.check(text_preprocessing_result, user, params) for item in self.items)
        for i, checked in enumerate(check_results):
            if checked:
                item = self.items[i]
                result = await item.internal_item.run(user, text_preprocessing_result, params)
                choice_is_made = True
                break
        if not choice_is_made and self._else_item:
            result = await self.else_item.run(user, text_preprocessing_result, params)
        return result


class ChoiceAction(Action):
    version: Optional[int]
    requirement_actions: RequirementAction
    else_action: Action

    FIELD_REQUIREMENT_KEY = "requirement_actions"
    FIELD_ELSE_KEY = "else_action"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(ChoiceAction, self).__init__(items, id)
        self._requirement_items = items[self.FIELD_REQUIREMENT_KEY]
        self._else_item = items.get(self.FIELD_ELSE_KEY)

        self.items = self.build_items()

        if self._else_item:
            self.else_item = self.build_else_item()
        else:
            self.else_item = None

    @list_factory(RequirementAction)
    def build_items(self):
        return self._requirement_items

    @factory(Action)
    def build_else_item(self):
        return self._else_item

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        result = None
        choice_is_made = False
        for item in self.items:
            if await item.requirement.check(text_preprocessing_result, user, params):
                result = await item.internal_item.run(user, text_preprocessing_result, params)
                choice_is_made = True
                break
        if not choice_is_made and self._else_item:
            result = await self.else_item.run(user, text_preprocessing_result, params)
        return result


class ElseAction(Action):
    version: Optional[int]
    action: Requirement
    else_action: Optional[Action]

    FIELD_ITEM_KEY = "action"
    FIELD_ELSE_KEY = "else_action"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(ElseAction, self).__init__(items, id)
        self._requirement = items["requirement"]
        self._item = items[self.FIELD_ITEM_KEY]
        self._else_item = items.get(self.FIELD_ELSE_KEY)

        self.requirement = self.build_requirement()
        self.item = self.build_item()
        if self._else_item:
            self.else_item = self.build_else_item()
        else:
            self.else_item = None

    @factory(Requirement)
    def build_requirement(self):
        return self._requirement

    @factory(Action)
    def build_item(self):
        return self._item

    @factory(Action)
    def build_else_item(self):
        return self._else_item

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Optional[Dict[str, Union[str, float, int]]]] = None) -> Optional[List[Command]]:
        result = None
        if await self.requirement.check(text_preprocessing_result, user, params):
            result = await self.item.run(user, text_preprocessing_result, params)
        elif self._else_item:
            result = await self.else_item.run(user, text_preprocessing_result, params)
        return result


class CompositeAction(Action):
    version: Optional[int]
    actions: List[Action]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(CompositeAction, self).__init__(items, id)
        self._actions = items.get("actions") or []
        self.actions = self.build_actions()

    @list_factory(Action)
    def build_actions(self):
        return self._actions

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        commands = []
        for action in self.actions:
            action_result = await action.run(user, text_preprocessing_result, params)
            if action_result:
                commands += action_result
        return commands


class NonRepeatingAction(CompositeAction):
    version: Optional[int]
    actions: List[Action]
    last_action_ids_storage: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(NonRepeatingAction, self).__init__(items, id)
        self._actions_count = len(items["actions"])
        self._last_action_ids_storage = items["last_action_ids_storage"]

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        last_ids = user.last_action_ids[self._last_action_ids_storage]
        all_indexes = list(range(self._actions_count))
        max_last_ids_count = self._actions_count - 1
        # get last_actions_ids slice with max_len of max_last_ids_count
        last_actions_ids = last_ids.get_list()[-max_last_ids_count:]
        available_indexes = list(set(all_indexes) - set(last_actions_ids))
        action_index = random.choice(available_indexes)
        action = self.actions[action_index]
        last_ids.add(action_index)
        result = await action.run(user, text_preprocessing_result, params)
        return result


class RandomAction(Action):

    def __init__(self, items, id=None):
        super().__init__(items, id)
        self._raw_actions = items["actions"]
        self.actions = self.build_actions()

    @list_factory(Action)
    def build_actions(self):
        return self._raw_actions

    async def run(self, user, text_preprocessing_result, params=None):
        pos = random.randint(0, len(self._raw_actions) - 1)
        action = self.actions[pos]
        command_list = await action.run(user, text_preprocessing_result, params=params)
        return command_list
