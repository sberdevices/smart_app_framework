import unittest
from unittest.mock import Mock

from scenarios.scenario_models.field.field_filler_description import FieldFillerDescription, PreviousMessagesFiller
from core.model.registered import registered_factories
from scenarios.scenario_models.field.field_filler_description import field_filler_description, field_filler_factory


class MockFiller:
    def __init__(self, items=None):
        self.count = 0

    def extract(self, text_preprocessing_result, user, params):
        self.count += 1


class PreviousMessagesFillerTest(unittest.TestCase):
    def test_fill_1(self):
        registered_factories[FieldFillerDescription] = field_filler_factory
        field_filler_description["mock_filler"] = MockFiller
        expected = "first"
        items = {"filler": {"type": "mock_filler", "result": expected}}
        user = Mock()
        user.preprocessing_messages_for_scenarios = Mock()
        user.preprocessing_messages_for_scenarios.processed_items = [{}, {}, {}]
        filler = PreviousMessagesFiller(items)
        filler.extract(None, user)
        self.assertEqual(filler.filler.count, 4)

    def test_fill_2(self):
        registered_factories[FieldFillerDescription] = field_filler_factory
        field_filler_description["mock_filler"] = MockFiller
        expected = "first"
        items = {"filler": {"type": "mock_filler", "result": expected}, "count": 2}
        user = Mock()
        user.preprocessing_messages_for_scenarios = Mock()
        user.preprocessing_messages_for_scenarios.processed_items = [{}, {}, {}]
        filler = PreviousMessagesFiller(items)
        filler.extract(None, user)
        self.assertEqual(filler.filler.count, 2)
