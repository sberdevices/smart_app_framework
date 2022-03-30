import unittest

from core.basic_models.actions.command import Command
from core.basic_models.actions.smartrating import CallRatingAction, AskRatingAction
from smart_kit.utils.picklable_mock import PicklableMagicMock
from tests.core_tests.basic_scenario_models_test.action_test.test_action import MockSimpleParametrizer


class CallRatingActionTest(unittest.TestCase):
    def test_run(self):
        expected = [Command("CALL_RATING", {}, None, "kafka",
                            {"topic_key": "toDP", "kafka_key": "main", "kafka_replyTopic": "app"})]
        user = PicklableMagicMock()
        params = {"params": "params"}
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        user.settings = {"template_settings": {"project_id": "0", "consumer_topic": "app"}}
        items = {}
        action = CallRatingAction(items)
        result = action.run(user, None)
        self.assertEqual(expected[0].name, result[0].name)
        self.assertEqual(expected[0].payload, result[0].payload)
        self.assertEqual(expected[0].request_data, result[0].request_data)


class AskRatingActionTest(unittest.TestCase):
    def test_run(self):
        expected = [Command("ASK_RATING", {}, None, "kafka",
                            {"topic_key": "toDP", "kafka_key": "main", "kafka_replyTopic": "app"})]
        user = PicklableMagicMock()
        params = {"params": "params"}
        user.parametrizer = MockSimpleParametrizer(user, {"data": params})
        user.settings = {"template_settings": {"project_id": "0", "consumer_topic": "app"}}
        items = {}
        action = AskRatingAction(items)
        result = action.run(user, None)
        self.assertEqual(expected[0].name, result[0].name)
        self.assertEqual(expected[0].payload, result[0].payload)
        self.assertEqual(expected[0].request_data, result[0].request_data)
