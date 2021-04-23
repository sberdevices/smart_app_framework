# coding: utf-8
import unittest
from unittest.mock import Mock, MagicMock, patch

from core.basic_models.answer_items.answer_items import SdkAnswerItem, items_factory, answer_items, BubbleText, \
    ItemCard, PronounceText, SuggestText, SuggestDeepLink
from core.unified_template.unified_template import UnifiedTemplate, UNIFIED_TEMPLATE_TYPE_NAME
from core.basic_models.actions.basic_actions import Action, DoingNothingAction, action_factory, RequirementAction, \
    actions, ChoiceAction, ElseAction, CompositeAction, NonRepeatingAction
from core.basic_models.actions.string_actions import StringAction, AfinaAnswerAction, SDKAnswer, \
    SDKAnswerToUser, NodeAction
from core.basic_models.actions.counter_actions import CounterIncrementAction, CounterDecrementAction, \
    CounterClearAction, CounterSetAction, CounterCopyAction
from core.basic_models.actions.external_actions import ExternalAction
from core.basic_models.actions.command import Command
from core.basic_models.requirement.basic_requirements import requirement_factory, Requirement, requirements
from core.model.registered import registered_factories


class MockParametrizer:
    def __init__(self, user, items=None):
        self.items = items or {}
        self.user = user
        self.data = items.get("data") or {}
        self.filter = items.get("filter") or False

    def collect(self, text_preprocessing_result=None, filter_params=None):
        data = {
            "payload": self.user.message.payload
        }
        data.update(self.data)
        if self.filter:
            data.update({"filter": "filter_out"})
        return data


class MockAction:
    def __init__(self, items=None):
        items = items or {}
        self.result = items.get("result")

    def run(self, user, text_preprocessing_result, params=None):
        return self.result or ["test action run"]


class UserMockAction:
    def __init__(self, items=None):
        items = items or {}
        self.result = items.get("result")
        self.done = False

    def run(self, user, text_preprocessing_result, params=None):
        self.done = True


class MockRequirement:
    def __init__(self, items):
        self.result = items.get("result")

    def check(self, text_preprocessing_result, user, params):
        return self.result


class MockSimpleParametrizer:
    def __init__(self, user, items=None):
        self.user = user
        self.data = items.get("data")

    def collect(self, text_preprocessing_result, filter_params=None):
        return self.data


class ActionTest(unittest.TestCase):
    def test_nodes_1(self):
        items = {"nodes": {"answer": "test"}}
        action = NodeAction(items)
        nodes = action.nodes
        action_key = list(nodes.keys())[0]
        self.assertEqual(action_key, 'answer')
        self.assertIsInstance(nodes[action_key], UnifiedTemplate)

    def test_nodes_2(self):
        items = {}
        action = NodeAction(items)
        nodes = action.nodes
        self.assertEqual(nodes, {})

    def test_base(self):
        items = {"nodes": "test"}
        action = Action(items)
        try:
            action.run(None, None)
            result = False
        except NotImplementedError:
            result = True
        self.assertEqual(result, True)

    def test_external(self):
        items = {"action": "test_action_key"}
        action = ExternalAction(items)
        user = Mock()
        user.descriptions = {"external_actions": {"test_action_key": MockAction()}}
        self.assertEqual(action.run(user, None), ["test action run"])

    def test_doing_nothing_action(self):
        items = {"nodes": {"answer": "test"}, "command": "test_name"}
        action = DoingNothingAction(items)
        result = action.run(None, None)
        self.assertIsInstance(result, list)
        command = result[0]
        self.assertIsInstance(command, Command)
        self.assertEqual(command.name, "test_name")
        self.assertEqual(command.payload, {"answer": "test"})

    def test_requirement_action(self):
        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        items = {"requirement": {"type": "test", "result": True}, "action": {"type": "test"}}
        action = RequirementAction(items)
        self.assertIsInstance(action.requirement, MockRequirement)
        self.assertIsInstance(action.internal_item, MockAction)
        self.assertEqual(action.run(None, None), ["test action run"])
        items = {"requirement": {"type": "test", "result": False}, "action": {"type": "test"}}
        action = RequirementAction(items)
        result = action.run(None, None)
        self.assertIsNone(result)

    def test_requirement_choice(self):
        items = {"requirement_actions": [
            {"requirement": {"type": "test", "result": False}, "action": {"type": "test", "result": "action1"}},
            {"requirement": {"type": "test", "result": True}, "action": {"type": "test", "result": "action2"}}
        ]}
        choice_action = ChoiceAction(items)
        self.assertIsInstance(choice_action.items, list)
        self.assertIsInstance(choice_action.items[0], RequirementAction)
        result = choice_action.run(None, None)
        self.assertEqual(result, "action2")

    def test_requirement_choice_else(self):
        items = {
            "requirement_actions": [
                {"requirement": {"type": "test", "result": False}, "action": {"type": "test", "result": "action1"}},
                {"requirement": {"type": "test", "result": False}, "action": {"type": "test", "result": "action2"}},
            ],
            "else_action": {"type": "test", "result": "action3"}
        }
        choice_action = ChoiceAction(items)
        self.assertIsInstance(choice_action.items, list)
        self.assertIsInstance(choice_action.items[0], RequirementAction)
        result = choice_action.run(None, None)
        self.assertEqual(result, "action3")

    def test_string_action(self):
        expected = [Command("cmd_id", {"item": "template", "params": "params"})]
        user = MagicMock()
        template = Mock()
        template.get_template = Mock(return_value=["nlpp.payload.personInfo.identityCard"])
        user.descriptions = {"render_templates": template}
        params = {"params": "params"}
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        items = {"command": "cmd_id",
                 "nodes":
                     {"item": "template", "params": "{{params}}"}}
        action = StringAction(items)
        result = action.run(user, None)
        self.assertEqual(expected[0].name, result[0].name)
        self.assertEqual(expected[0].payload, result[0].payload)

    def test_else_action_if(self):
        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        user = Mock()
        items = {
            "requirement": {"type": "test", "result": True},
            "action": {"type": "test", "result": "main_action"},
            "else_action": {"type": "test", "result": "else_action"}
        }
        action = ElseAction(items)
        self.assertEqual(action.run(user, None), "main_action")

    def test_else_action_else(self):
        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        user = Mock()
        items = {
            "requirement": {"type": "test", "result": False},
            "action": {"type": "test", "result": "main_action"},
            "else_action": {"type": "test", "result": "else_action"}
        }
        action = ElseAction(items)
        self.assertEqual(action.run(user, None), "else_action")

    def test_else_action_no_else_if(self):
        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        user = Mock()
        items = {
            "requirement": {"type": "test", "result": True},
            "action": {"type": "test", "result": "main_action"},
        }
        action = ElseAction(items)
        self.assertEqual(action.run(user, None), "main_action")

    def test_else_action_no_else_else(self):
        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        registered_factories[Action] = action_factory
        actions["test"] = MockAction
        user = Mock()
        items = {
            "requirement": {"type": "test", "result": False},
            "action": {"type": "test", "result": "main_action"},
        }
        action = ElseAction(items)
        result = action.run(user, None)
        self.assertIsNone(result)

    def test_composite_action(self):
        registered_factories[Action] = action_factory
        actions["action_mock"] = MockAction
        user = Mock()
        items = {
            "actions": [
                {"type": "action_mock"},
                {"type": "action_mock"}
            ]
        }
        action = CompositeAction(items)
        result = action.run(user, None)
        self.assertEqual(['test action run', 'test action run'], result)

    def test_node_action_support_templates(self):
        params = {
            "markup": "italic",
            "email": "heyho@sberbank.ru",
            "name": "Buratino"
        }
        items = {
            "support_templates": {
                "markup": "{%if markup=='italic'%}i{% else %}b{% endif %}",
                "email": "{%if email%}<{{markup}}>Email: {{email}}</{{markup}}>\n{% endif %}",
                "name": "{%if name%}<{{markup}}>Name: {{name}}</{{markup}}>\n{% endif %}",
                "result": "{{email}}{{name}}"
            },
            "nodes": {
                "answer": "{{result|trim}}"
            }
        }
        expected = "<i>Email: heyho@sberbank.ru</i>\n<i>Name: Buratino</i>"

        action = StringAction(items)
        for template_key, template in action.support_templates.items():
            self.assertIsInstance(template, UnifiedTemplate)
        user = MagicMock()
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        output = action.run(user=user, text_preprocessing_result=None)[0].payload["answer"]
        self.assertEqual(output, expected)

    def test_string_action_support_templates(self):
        params = {
            "answer_text": "some_text",
            "buttons_number": 3
        }
        items = {
            "nodes": {
                "answer": "{{ answer_text }}",
                "buttons": {
                    "type": UNIFIED_TEMPLATE_TYPE_NAME,
                    "template": "{{range(buttons_number)|list}}",
                    "loader": "json"
                }
            }
        }
        expected = {
            "answer": "some_text",
            "buttons": [0, 1, 2]
        }
        action = StringAction(items)
        user = MagicMock()
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        output = action.run(user=user, text_preprocessing_result=None)[0].payload
        self.assertEqual(output, expected)


class NonRepeatingActionTest(unittest.TestCase):
    def setUp(self):
        self.expected = Mock()
        self.expected1 = Mock()
        self.action = NonRepeatingAction({"actions": [{"type": "action_mock",
                                                       "result": self.expected},
                                                      {"type": "action_mock",
                                                       "result": self.expected1}
                                                      ],
                                          "last_action_ids_storage": "last_action_ids_storage"})
        self.user = MagicMock()
        registered_factories[Action] = action_factory
        actions["action_mock"] = MockAction

    def test_run_available_indexes(self):
        self.user.last_action_ids["last_action_ids_storage"].get_list.side_effect = [[0]]
        result = self.action.run(self.user, None)
        self.user.last_action_ids["last_action_ids_storage"].add.assert_called_once()
        self.assertEqual(result, self.expected1)

    def test_run_no_available_indexes(self):
        self.user.last_action_ids["last_action_ids_storage"].get_list.side_effect = [[0, 1]]
        result = self.action.run(self.user, None)
        self.assertEqual(result, self.expected)


class CounterIncrementActionTest(unittest.TestCase):
    def test_run(self):
        user = Mock()
        counter = Mock()
        counter.inc = Mock()
        user.counters = {"test": counter}
        items = {"key": "test"}
        action = CounterIncrementAction(items)
        action.run(user, None)
        user.counters["test"].inc.assert_called_once()


class CounterDecrementActionTest(unittest.TestCase):
    def test_run(self):
        user = Mock()
        counter = Mock()
        counter.dec = Mock()
        user.counters = {"test": counter}
        items = {"key": "test"}
        action = CounterDecrementAction(items)
        action.run(user, None)
        user.counters["test"].dec.assert_called_once()


class CounterClearActionTest(unittest.TestCase):
    def test_run(self):
        user = Mock()
        user.counters = Mock()
        user.counters.inc = Mock()
        items = {"key": "test"}
        action = CounterClearAction(items)
        action.run(user, None)
        user.counters.clear.assert_called_once()


class CounterSetActionTest(unittest.TestCase):
    def test_run(self):
        user = Mock()
        counter = Mock()
        counter.inc = Mock()
        counters = {"test": counter}
        user.counters = counters
        items = {"key": "test"}
        action = CounterSetAction(items)
        action.run(user, None)
        user.counters["test"].set.assert_called_once()


class CounterCopyActionTest(unittest.TestCase):
    def test_run(self):
        user = Mock()
        counter_src = Mock()
        counter_src.value = 10
        counter_dst = Mock()
        user.counters = {"src": counter_src, "dst": counter_dst}
        items = {"source": "src", "destination": "dst"}
        action = CounterCopyAction(items)
        action.run(user, None)
        user.counters["dst"].set.assert_called_once_with(user.counters["src"].value,
                                                         action.reset_time, action.time_shift)


class AfinaAnswerActionTest(unittest.TestCase):
    def test_typical_answer(self):
        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        expected = [MagicMock(_name="ANSWER_TO_USER", raw={'messageName': 'ANSWER_TO_USER',
                                                           'payload': {'answer': 'a1'}})]
        items = {
            "nodes": {
                "answer": ["a1", "a1", "a1"],
            }
        }
        action = AfinaAnswerAction(items)

        result = action.run(user, None)
        self.assertEqual(expected[0]._name, result[0].name)
        self.assertEqual(expected[0].raw, result[0].raw)

    def test_typical_answer_with_other(self):
        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        expected = [MagicMock(_name="ANSWER_TO_USER", raw={'messageName': 'ANSWER_TO_USER',
                                                           'payload': {'answer': 'a1',
                                                                       "pronounce_text": 'pt2',
                                                                       "picture": "1.jpg"}})]
        items = {
            "nodes": {
                "answer": ["a1", "a1", "a1"],
                "pronounce_text": ["pt2"],
                "picture": ["1.jpg", "1.jpg", "1.jpg"]
            }
        }
        action = AfinaAnswerAction(items)

        result = action.run(user, None)
        self.assertEqual(expected[0]._name, result[0].name)
        self.assertEqual(expected[0].raw, result[0].raw)

    def test_typical_answer_with_pers_info(self):
        expected = [MagicMock(_name="ANSWER_TO_USER", raw={'messageName': 'ANSWER_TO_USER',
                                                           'payload': {'answer': 'Ivan Ivanov'}})]
        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = Mock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {"nodes": {"answer": ["{{payload.personInfo.name}}"]}}
        action = AfinaAnswerAction(items)
        result = action.run(user, None)
        self.assertEqual(expected[0]._name, result[0].name)
        self.assertEqual(expected[0].raw, result[0].raw)

    def test_items_empty(self):
        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        template = Mock()
        template.get_template = Mock(return_value=[])
        user.descriptions = {"render_templates": template}
        items = None
        action = AfinaAnswerAction(items)
        result = action.run(user, None)
        self.assertEqual(result, [])

    def test__items_empty_dict(self):
        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        template = Mock()
        template.get_template = Mock(return_value=[])
        user.descriptions = {"render_templates": template}
        items = {}
        action = AfinaAnswerAction(items)
        result = action.run(user, None)
        self.assertEqual(result, [])


class CardAnswerActionTest(unittest.TestCase):
    def test_typical_answer(self):
        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = Mock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {
            "type": "sdk_answer",
            "nodes": {
                "pronounceText": ["pronounceText1", "{{payload.personInfo.name}}"],
                "items": [
                  {
                    "bubble": {
                      "text": ["Text1", "Text2"]
                    }
                  },
                  {
                    "card": {
                      "type": "simple_list",
                      "header": "1 доллар США ",
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
                      "footer": "{{payload.personInfo.name}} Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD"
                    }
                  }
                ],
                "suggestions": {
                     "buttons": [{
                        "title": ["Отделения"],
                        "action": {
                          "text": "Где ближайщие отделения сбера?",
                          "type": "text"
                        }
                     }]
                }
            }
        }
        exp1 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'Ivan Ivanov', 'items': [{'bubble': {'text': 'Text1'}}, {'card': {'type': 'simple_list', 'header': '1 доллар США ', 'items': [{'title': 'Купить', 'body': '67.73 RUR'}, {'title': 'Продать', 'body': '64.56 RUR'}], 'footer': 'Ivan Ivanov Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD'}}], 'suggestions': {'buttons': [{'title': 'Отделения', 'action': {'text': 'Где ближайщие отделения сбера?', 'type': 'text'}}]}}}"
        exp2 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'Ivan Ivanov', 'items': [{'bubble': {'text': 'Text2'}}, {'card': {'type': 'simple_list', 'header': '1 доллар США ', 'items': [{'title': 'Купить', 'body': '67.73 RUR'}, {'title': 'Продать', 'body': '64.56 RUR'}], 'footer': 'Ivan Ivanov Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD'}}], 'suggestions': {'buttons': [{'title': 'Отделения', 'action': {'text': 'Где ближайщие отделения сбера?', 'type': 'text'}}]}}}"
        exp3 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'items': [{'bubble': {'text': 'Text1'}}, {'card': {'type': 'simple_list', 'header': '1 доллар США ', 'items': [{'title': 'Купить', 'body': '67.73 RUR'}, {'title': 'Продать', 'body': '64.56 RUR'}], 'footer': 'Ivan Ivanov Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD'}}], 'suggestions': {'buttons': [{'title': 'Отделения', 'action': {'text': 'Где ближайщие отделения сбера?', 'type': 'text'}}]}}}"
        exp4 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'items': [{'bubble': {'text': 'Text2'}}, {'card': {'type': 'simple_list', 'header': '1 доллар США ', 'items': [{'title': 'Купить', 'body': '67.73 RUR'}, {'title': 'Продать', 'body': '64.56 RUR'}], 'footer': 'Ivan Ivanov Сбербанк Онлайн на сегодня 17:53 при обмене до 1000 USD'}}], 'suggestions': {'buttons': [{'title': 'Отделения', 'action': {'text': 'Где ближайщие отделения сбера?', 'type': 'text'}}]}}}"
        expect_arr = [exp1, exp2, exp3, exp4]
        for i in range(10):
            action = SDKAnswer(items)
            result = action.run(user, None)
            self.assertEqual("ANSWER_TO_USER", result[0].name)
            self.assertTrue(str(result[0].raw) in expect_arr)


    def test_typical_answer_without_items(self):
        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = Mock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {
            "type": "sdk_answer",
            "nodes": {
                "pronounceText": ["pronounceText1", "pronounceText2"],
            }
        }
        exp1 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1'}}"
        exp2 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1'}}"
        exp3 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText2'}}"
        exp4 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText2'}}"
        exp_list = [exp1, exp2, exp3, exp4]
        for i in range(10):
            action = SDKAnswer(items)
            result = action.run(user, None)
            self.assertEqual("ANSWER_TO_USER", result[0].name)
            self.assertTrue(str(result[0].raw) in exp_list)

    def test_typical_answer_without_nodes(self):
        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = Mock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {
                "type": "sdk_answer",
                "pronounceText": ["pronounceText1"],
                "suggestions": {
                    "buttons": [
                        {
                            "title": ["{{payload.personInfo.name}}", "отделения2"],
                            "action": {
                                "text": "отделения",
                                "type": "text"
                            }
                        },
                        {
                            "title": ["кредит1", "кредит2"],
                            "action": {
                                "text": "кредит",
                                "type": "text"
                            }
                        }
                    ]
                }
        }
        exp1 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'suggestions': {'buttons': [{'title': 'Ivan Ivanov', 'action': {'text': 'отделения', 'type': 'text'}}, {'title': 'кредит1', 'action': {'text': 'кредит', 'type': 'text'}}]}}}"
        exp2 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'suggestions': {'buttons': [{'title': 'Ivan Ivanov', 'action': {'text': 'отделения', 'type': 'text'}}, {'title': 'кредит2', 'action': {'text': 'кредит', 'type': 'text'}}]}}}"
        exp3 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'suggestions': {'buttons': [{'title': 'отделения2', 'action': {'text': 'отделения', 'type': 'text'}}, {'title': 'кредит1', 'action': {'text': 'кредит', 'type': 'text'}}]}}}"
        exp4 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'pronounceText1', 'suggestions': {'buttons': [{'title': 'отделения2', 'action': {'text': 'отделения', 'type': 'text'}}, {'title': 'кредит2', 'action': {'text': 'кредит', 'type': 'text'}}]}}}"
        expect_arr = [exp1, exp2, exp3, exp4]
        for i in range(10):
            action = SDKAnswer(items)
            result = action.run(user, None)
            self.assertEqual("ANSWER_TO_USER", result[0].name)
            self.assertTrue(str(result[0].raw) in expect_arr)


class SDKRandomAnswer(unittest.TestCase):
    def test_SDKItemAnswer_full(self):

        registered_factories[SdkAnswerItem] = items_factory
        answer_items["bubble_text"] = BubbleText
        answer_items["item_card"] = ItemCard
        answer_items["pronounce_text"] = PronounceText
        answer_items["suggest_text"] = SuggestText
        answer_items["suggest_deeplink"] = SuggestDeepLink

        registered_factories[Requirement] = requirement_factory
        requirements["test"] = MockRequirement
        requirements[None] = Requirement

        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = Mock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {
            "type": "sdk_answer_to_user",
            "static":
                {
                    "static_text": "st1",
                    "card1": {"cards_params": "a lot of params"},
                    "dl": "www.ww.w"
                },
            "random_choice": [
                {
                    "pron": "p1",
                    "txt": "{{payload.personInfo.name}}",
                    "title": "title1"
                },
                {
                    "pron": "p2",
                    "txt": "t2",
                    "title": "title2"
                }],
            "items":
                [
                    {
                        'type': "item_card",
                        "text": "txt",
                        "requirement": {"type": "test", "result": False}
                    },
                    {
                        'type': "bubble_text",
                        "text": "txt",
                        "markdown": False
                    },
                    {
                        'type': "item_card",
                        "text": "card1",
                        "requirement": {"type": "test", "result": True}
                    }
                ],
            "root":
                [
                    {
                        'type': "pronounce_text",
                        "text": "pron",
                    }
                ],
            "suggestions":
                [
                    {
                        "type": "suggest_text",
                        "title": "pron",
                        "text": "txt",
                    },
                    {
                        "type": "suggest_text",
                        "title": "pron",
                        "text": "txt",
                        "requirement": {"type": "test", "result": True}
                    },
                    {
                        "type": "suggest_deeplink",
                        "title": "pron",
                        "deep_link": "dl"
                    }
                ]
        }
        exp1 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'items': [{'bubble': {'text': 't2', 'markdown': False}}, {'card': {'cards_params': 'a lot of params'}}], 'suggestions': {'buttons': [{'title': 'p2', 'action': {'text': 't2', 'type': 'text'}}, {'title': 'p2', 'action': {'text': 't2', 'type': 'text'}}, {'title': 'p2', 'action': {'deep_link': 'www.ww.w', 'type': 'deep_link'}}]}, 'pronounceText': 'p2'}}"
        exp2 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'items': [{'bubble': {'text': 'Ivan Ivanov', 'markdown': False}}, {'card': {'cards_params': 'a lot of params'}}], 'suggestions': {'buttons': [{'title': 'p1', 'action': {'text': 'Ivan Ivanov', 'type': 'text'}}, {'title': 'p1', 'action': {'text': 'Ivan Ivanov', 'type': 'text'}}, {'title': 'p1', 'action': {'deep_link': 'www.ww.w', 'type': 'deep_link'}}]}, 'pronounceText': 'p1'}}"

        action = SDKAnswerToUser(items)
        for i in range(3):
            result = action.run(user, None)
            self.assertTrue(str(result[0].raw) in [exp1, exp2])

    def test_SDKItemAnswer_root(self):

        registered_factories[SdkAnswerItem] = items_factory
        answer_items["bubble_text"] = BubbleText
        answer_items["item_card"] = ItemCard
        answer_items["pronounce_text"] = PronounceText
        answer_items["suggest_text"] = SuggestText
        answer_items["suggest_deeplink"] = SuggestDeepLink


        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        user.message = Mock()
        user.message.payload = {"personInfo": {"name": "Ivan Ivanov"}}
        items = {
            "type": "sdk_answer_to_user",
            "static":
                {
                    "static_text": "st1",
                    "card1": {"cards_params": "a lot of params"},
                    "dl": "www.ww.w"
                },
            "random_choice": [
                {
                    "pron": "p1",
                    "txt": "{{payload.personInfo.name}}",
                    "title": "title1"
                },
                {
                    "pron": "p2",
                    "txt": "t2",
                    "title": "title2"
                }],
            "root":
                [
                    {
                        'type': "pronounce_text",
                        "text": "pron",
                    },
                ]
        }
        exp1 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'p1'}}"
        exp2 = "{'messageName': 'ANSWER_TO_USER', 'payload': {'pronounceText': 'p2'}}"

        action = SDKAnswerToUser(items)
        for i in range(3):
            result = action.run(user, None)
            self.assertTrue(str(result[0].raw) in [exp1, exp2])

    def test_SDKItemAnswer_simple(self):

        registered_factories[SdkAnswerItem] = items_factory
        answer_items["bubble_text"] = BubbleText

        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        items = {
            "type": "sdk_answer_to_user",
            "items":
                [
                    {
                        'type': "bubble_text",
                        "text": "42"
                    }
                ]
        }
        action = SDKAnswerToUser(items)
        result = action.run(user, None)
        self.assertDictEqual(result[0].raw, {'messageName': 'ANSWER_TO_USER', 'payload': {'items': [{'bubble': {'text': '42', 'markdown': True}}]}})

    def test_SDKItemAnswer_suggestions_template(self):

        registered_factories[SdkAnswerItem] = items_factory
        answer_items["bubble_text"] = BubbleText

        user = Mock()
        user.parametrizer = MockParametrizer(user, {})
        items = {
            "type": "sdk_answer_to_user",
            "support_templates": {
                "suggestions_from_template": '{ "buttons": [ { "title": "some title", "action": { "type": "text", "text": "some text" } } ]}'
            },
            "suggestions_template": {
                "type": "unified_template",
                "template": "{{ suggestions_from_template }}",
                "loader": "json"
            }
        }
        action = SDKAnswerToUser(items)
        result = action.run(user, None)
        self.assertDictEqual(
            result[0].raw,
            {
                'messageName': 'ANSWER_TO_USER',
                'payload': {
                    'suggestions': {
                        'buttons': [
                            {'title': 'some title', 'action': {'type': 'text', 'text': 'some text'}}
                        ]
                    }
                }
            })
