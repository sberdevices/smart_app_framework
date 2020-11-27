# coding: utf-8
import unittest
from unittest.mock import Mock
from core.basic_models.actions.basic_actions import Action, actions, action_factory
from core.model.registered import registered_factories
from scenarios.behaviors.behavior_description import BehaviorDescription


class MockAction(Action):
    def run(self, user, text_preprocessing_result, params=None):
        return []


class TestAction:
    def __init__(self):
        self.id = '123-456-789'
        self.version = 21  # какая-то версия

    def run(self, a, b, c):
        return 123   # некий результат


class BehaviorDescriptionTest(unittest.TestCase):

    def setUp(self):
        self.test_items = {"success_action": [TestAction()]}
        self.test_user = Mock()
        self.test_user.settings = {"template_settings": {}}
        registered_factories[Action] = action_factory
        actions[None] = MockAction

    def test_create(self):
        behavior_description = BehaviorDescription({"success_action": None, "fail_action": None, "timeout": 10})
        self.assertEqual(behavior_description.timeout(self.test_user), 10)
        self.assertIsInstance(behavior_description.success_action, Action)
        self.assertIsInstance(behavior_description.fail_action, Action)

    def test_behavior_description_init(self):
        obj = BehaviorDescription(self.test_items)
        self.assertTrue(obj.timeout(self.test_user) == 300)  # значение из scenarios.behaviors.behavior_description