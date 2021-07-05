# coding: utf-8
import random
from copy import copy
from typing import Union, Dict, List, Any, Optional

from lazy import lazy

from core.basic_models.actions.basic_actions import CommandAction
from core.basic_models.actions.command import Command
from core.basic_models.answer_items.answer_items import SdkAnswerItem
from core.model.base_user import BaseUser
from core.model.factory import list_factory
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate, UNIFIED_TEMPLATE_TYPE_NAME

ANSWER_TO_USER = "ANSWER_TO_USER"


class NodeAction(CommandAction):
    version: Optional[int]
    command: str
    nodes: Dict[str, List[List[str]]]
    support_templates: Dict[str, str]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(NodeAction, self).__init__(items, id)
        items = items or {}
        self._nodes = items.get("nodes") or {}
        self._support_templates = items.get("support_templates") or {}
        self.no_empty_nodes = items.get("no_empty_nodes", False)

    @lazy
    def nodes(self):
        return {k: self._get_template_tree(t) for k, t in self._nodes.items()}

    @lazy
    def support_templates(self):
        return {k: self._get_template_tree(t) for k, t in self._support_templates.items()}

    def _get_template_tree(self, value):
        is_dict_unified_template = isinstance(value, dict) and value.get("type") == UNIFIED_TEMPLATE_TYPE_NAME
        if isinstance(value, str) or is_dict_unified_template:
            result = UnifiedTemplate(value)
        elif isinstance(value, dict):
            result = {}
            for inner_key, inner_value in value.items():
                result[inner_key] = self._get_template_tree(inner_value)
        elif isinstance(value, list):
            result = []
            for inner_value in value:
                result.append(self._get_template_tree(inner_value))
        else:
            result = value
        return result

    def _get_rendered_tree(self, value, params, no_empty=False):
        params = copy(params)
        for support_key, support_template in self.support_templates.items():
            params[support_key] = support_template.render(params)
        return self._get_rendered_tree_recursive(value, params, no_empty=no_empty)

    def _get_rendered_tree_recursive(self, value, params, no_empty=False):
        value_type = type(value)
        if value_type is dict:
            result = {}
            for inner_key, inner_value in value.items():
                rendered = self._get_rendered_tree_recursive(inner_value, params, no_empty=no_empty)
                if rendered != "" or not no_empty:
                    result[inner_key] = rendered
        elif value_type is list:
            result = []
            for inner_value in value:
                rendered = self._get_rendered_tree_recursive(inner_value, params, no_empty=no_empty)
                if rendered != "" or not no_empty:
                    result.append(rendered)

        elif value_type is UnifiedTemplate:
            result = value.render(params)
        else:
            result = value
        return result

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        raise NotImplementedError


class StringAction(NodeAction):
    """
    Example:
    {
      "pay_phone_cmd": {
        "type": "string",
        "command": "recharge_mobile",
        "nodes": {
          "phone": "{% if approve and phone_number is defined and phone_number not in (None, 1) %}{{ phone_number }}{% endif %}",
          "amount": "{% if approve and amount is defined %}{{ amount | int }}{% endif%}",
          "currency": "{% if approve and currency is defined %}{{ currency }}{% endif%}",
          "card": "{% if approve and card is defined %}{{ card }}{% endif %}"
        }
      }
    }
    """
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(StringAction, self).__init__(items, id)

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        # Example: Command("ANSWER_TO_USER", {"answer": {"key1": "string1", "keyN": "stringN"}})
        command_params = dict()
        params = params or {}
        collected = user.parametrizer.collect(text_preprocessing_result, filter_params={"command": self.command})
        params.update(collected)

        for key, value in self.nodes.items():
            rendered = self._get_rendered_tree(value, params, self.no_empty_nodes)
            if rendered != "" or not self.no_empty_nodes:
                command_params[key] = rendered

        commands = [Command(self.command, command_params, self.id, request_type=self.request_type,
                            request_data=self.request_data)]
        return commands


class AfinaAnswerAction(NodeAction):
    """
    Example:
    {
      "type": "random_field_answer",
      "nodes":
      {
          "pronounce_text": ["pronounceText1", "pronounceText2"]
      }
    }

    Output:
    [command1(pronounceText)]
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(AfinaAnswerAction, self).__init__(items, id)
        self.command: str = ANSWER_TO_USER

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        params = user.parametrizer.collect(text_preprocessing_result, filter_params={"command": self.command})
        answer_params = dict()
        result = []

        nodes = self.nodes.items() if self.nodes else []
        for key, template in nodes:
            if template:
                choice_index = random.randint(0, len(template) - 1)
                rendered = self._get_rendered_tree(template[choice_index], params, self.no_empty_nodes)
                if rendered != "" or not self.no_empty_nodes:
                    answer_params[key] = rendered

        if answer_params:
            result = [Command(self.command, answer_params, self.id, request_type=self.request_type,
                              request_data=self.request_data)]
        return result


class SDKAnswer(NodeAction):
    """
    Example:
    {
      "type": "sdk_answer",
      # можно без nodes
      "nodes":
      {
        "pronounceText": ["pronounceText1", "pronounceText2"],
        "items": [
          {
            "bubble": {
              "text": ["Text1", "Text2"]
            }
          },
          {
            "card": {
              "type": "simple_list",
              "header": "1 доллар США",
              "items": [
                {
                  "title": "Купить",
                  "body": "67.73 RUR"
                },
                {
                  "title": "Продать",
                  "body": "64.56 RUR"
                }
              ],
              "footer": "Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD"
            }
          }
        ],
        "suggestions": {
         "buttons": [{
            "title": "Отделения",
            "action": {
              "text": ["Где ближайщие отделения сбера?"],
              "type": "text"
            }
         }]
        }
      }
    }

    Output:
    [command1(pronounceTexti, Textj, card, buttons)]
    ответ c карточками с случайным выбором текстов из массива
    карточки на андроиде требуют sdk_version не ниже "20.03.0.0"
    """
    INDEX_WILDCARD = "*index*"
    RANDOM_PATH = [['items', INDEX_WILDCARD, 'bubble', 'text'], ['pronounceText'], ['suggestions', 'buttons', INDEX_WILDCARD, 'title']]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(SDKAnswer, self).__init__(items, id)
        self.command: str = ANSWER_TO_USER
        if self._nodes == {}:
            self._nodes = {i: items.get(i) for i in items if i not in ['random_paths', 'same_ans', 'type', 'support_templates', 'no_empty_nodes']}

    # функция идет по RANDOM_PATH, числа в нем считает индексами массива,
    # INDEX_WILDCARD - произвольным индексом массива, прочее - ключами словаря
    # в конце пути предполагается непустой массив, дойдя до которого из него выбирается случайный элемент
    def random_by_path(self, input_dict, nested_key):
        internal_dict_value = input_dict
        for ik, k in enumerate(nested_key):
            last_dict = internal_dict_value
            if k == self.INDEX_WILDCARD:
                for wildcard_item in last_dict:
                    self.random_by_path(wildcard_item, nested_key[ik + 1:])
                return
            if k.isdigit():
                internal_dict_value = internal_dict_value[int(k)]
            else:
                internal_dict_value = internal_dict_value.get(k, None)
            if internal_dict_value is None:
                return
        last_dict[k] = random.choice(last_dict[k])

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        result = []
        params = user.parametrizer.collect(text_preprocessing_result, filter_params={"command": self.command})
        rendered = self._get_rendered_tree(self.nodes, params, self.no_empty_nodes)
        for j in self.RANDOM_PATH:
            self.random_by_path(rendered, j)
        if rendered or not self.no_empty_nodes:
            result = [
                Command(
                    self.command,
                    rendered,
                    self.id,
                    request_type=self.request_type,
                    request_data=self.request_data,
                )
            ]
        return result


class SDKAnswerToUser(NodeAction):
    """
    Example:
    {
        "type": "sdk_answer_to_user",
        "root":
        [
          {
            "type": "pronounce_text",
            "text": "ans"
          }
        ],
        "static": {
          "ios_card": {
            "type": "list_card",
            "cells": [
              {
                "ios_params": "ios"
              }
            ]
          },
          "android_card": {
            "type": "list_card",
            "cells": [
              {
                "android_params": "android"
              }
            ]
          },
          "tittle1": "static tittle1",
          "tittle2": "static tittle2",
          "sg_dl": "www.www.www",
          "sg_text": "static suggest text"
        },
        "random_choice": [
          {
            "ans": "random text1"
          },
          {
            "ans": "random text2"
          }
        ],
        "items": [
          {
            "type": "item_card",
            "value": "ios_card",
            "requirement": {
              "type": "external",
              "requirement": "OCTOBER_iOS"
            }
          },
          {
            "type": "item_card",
            "value": "android_card",
            "requirement": {
              "type": "external",
              "requirement": "OCTOBER_android"
            }
          },
          {
            "type": "bubble_text",
            "text": "ans"
          }
        ],
        "suggestions": [
          {
            "type": "suggest_text",
            "text": "sg_text",
            "title": "tittle1"
          },
          {
            "type": "suggest_deeplink",
            "text": "sg_text",
            "deep_link": "tittle1"
          }
        ]
    }

    Output:
    {
        "items":
            [{
                "card": {"type": "list_card", "cells": [{"ios_params": "ios"}]}},
                {"bubble": {"text": "random texti", "markdown": True}
            }],
        "suggestions":
            {"buttons":
                [
                    {"title": "static tittle1", "action": {"text": "static suggest text", "type": "text"}},
                    {"title": "static tittle2", "action": {"deep_link": "www.www.www", "type": "deep_link"}}
                ]
            },
        "pronounceText": "random texti"
    }
    ответ c карточками с случайным выбором текстов из random_choice
    карточки на андроиде требуют sdk_version не ниже "20.03.0.0"
    """

    ITEMS = "items"
    SUGGESTIONS = "suggestions"
    SUGGESTIONS_TEMPLATE = "suggestions_template"
    BUTTONS = "buttons"
    STATIC = "static"
    RANDOM_CHOICE = "random_choice"
    COMMAND = "command"
    ROOT = "root"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(SDKAnswerToUser, self).__init__(items, id)
        self.command: str = ANSWER_TO_USER
        self._nodes[self.STATIC] = items.get(self.STATIC, {})
        self._nodes[self.RANDOM_CHOICE] = items.get(self.RANDOM_CHOICE, {})
        self._nodes[self.SUGGESTIONS] = items.get(self.SUGGESTIONS, {})
        self._nodes[self.SUGGESTIONS_TEMPLATE] = items.get(self.SUGGESTIONS_TEMPLATE, {})
        self._items = items.get(self.ITEMS, {})
        self._suggests = items.get(self.SUGGESTIONS, {})
        self._suggests_template = items.get(self.SUGGESTIONS_TEMPLATE)
        self._root = items.get(self.ROOT, {})

        self.items = self.build_items()
        self.suggests = self.build_suggests()
        self.root = self.build_root()

    @list_factory(SdkAnswerItem)
    def build_items(self):
        return self._items

    @list_factory(SdkAnswerItem)
    def build_suggests(self):
        return self._suggests

    @list_factory(SdkAnswerItem)
    def build_root(self):
        return self._root

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:

        result = []
        params = user.parametrizer.collect(text_preprocessing_result, filter_params={self.COMMAND: self.command})
        rendered = self._get_rendered_tree(self.nodes[self.STATIC], params, self.no_empty_nodes)
        if self._nodes[self.RANDOM_CHOICE]:
            random_node = random.choice(self.nodes[self.RANDOM_CHOICE])
            rendered_random = self._get_rendered_tree(random_node, params, self.no_empty_nodes)
            rendered.update(rendered_random)
        out = {}
        for item in self.items:
            if item.requirement.check(text_preprocessing_result, user, params):
                out.setdefault(self.ITEMS, []).append(item.render(rendered))

        if self._suggests_template is not None:
            out[self.SUGGESTIONS] = self._get_rendered_tree(self.nodes[self.SUGGESTIONS_TEMPLATE], params,
                                                            self.no_empty_nodes)
        else:
            for suggest in self.suggests:
                if suggest.requirement.check(text_preprocessing_result, user, params):
                    data_dict = out.setdefault(self.SUGGESTIONS, {self.BUTTONS: []})
                    buttons = data_dict[self.BUTTONS]
                    rendered_text = suggest.render(rendered)
                    buttons.append(rendered_text)
        for part in self.root:
            if part.requirement.check(text_preprocessing_result, user):
                out.update(part.render(rendered))
        if rendered or not self.no_empty_nodes:
            result = [
                Command(
                    self.command,
                    out,
                    self.id,
                    request_type=self.request_type,
                    request_data=self.request_data,
                )
            ]
        return result
