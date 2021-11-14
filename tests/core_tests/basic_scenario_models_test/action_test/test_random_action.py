from unittest import IsolatedAsyncioTestCase

from core.basic_models.actions.basic_actions import Action, action_factory, actions, DoingNothingAction, RandomAction
from core.model.registered import registered_factories


class TestRandomAction(IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        registered_factories[Action] = action_factory
        actions["do_nothing"] = DoingNothingAction

    async def test_1(self):

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
        result = await action.run(None, None)
        self.assertIsNotNone(result)

    async def test_2(self):
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
        result = await action.run(None, None)
        self.assertIsNotNone(result)
