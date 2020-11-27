from unittest import TestCase

from core.basic_models.actions.basic_actions import Action, action_factory, actions, DoingNothingAction, RandomAction
from core.model.registered import registered_factories


class TestRandomAction(TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        registered_factories[Action] = action_factory
        actions["do_nothing"] = DoingNothingAction

    def test_1(self):

        items = {
            "actions": [
                {
                    "type": "do_nothing",
                    "command": "ANSWER_TO_USER",
                    "nodes": {
                        "answer": "Доброе утро!",
                    }
                },
                {
                    "type": "do_nothing",
                    "command": "ANSWER_TO_USER",
                    "nodes": {
                        "answer": "Добрый вечер!",
                    }
                }
            ]
        }
        action = RandomAction(items, 5)
        result = action.run(None, None)
        self.assertIsNotNone(result)

    def test_2(self):
        items = {
            "actions": [
                {
                    "type": "do_nothing",
                    "command": "ANSWER_TO_USER",
                    "nodes": {
                        "answer": "Добрый вечер!",
                    }
                }
            ]
        }
        action = RandomAction(items, 5)
        result = action.run(None, None)
        self.assertIsNotNone(result)
