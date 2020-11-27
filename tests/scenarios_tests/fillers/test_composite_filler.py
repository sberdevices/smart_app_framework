from unittest import TestCase
from unittest.mock import Mock
from scenarios.scenario_models.field.field_filler_description import FieldFillerDescription, CompositeFiller

from core.model.registered import registered_factories
from scenarios.scenario_models.field.field_filler_description import field_filler_factory, field_filler_description


class MockFiller:
    def __init__(self, items=None):
        items = items or {}
        self.result = items.get("result")

    def extract(self, text_preprocessing_result, user, params):
        return self.result


class TestCompositeFiller(TestCase):

    @classmethod
    def setUpClass(cls):
        registered_factories[FieldFillerDescription] = field_filler_factory
        field_filler_description["mock_filler"] = MockFiller
        TestCompositeFiller.user = Mock()

    def test_first_filler(self):
        expected = "first"
        items = {
            "fillers": [
                {"type": "mock_filler", "result": expected},
                {"type": "mock_filler", "result": "second"}
            ]
        }
        filler = CompositeFiller(items)
        result = filler.extract(None, self.user)
        self.assertEqual(expected, result)

    def test_second_filler(self):
        expected = "second"
        items = {
            "fillers": [
                {"type": "mock_filler"},
                {"type": "mock_filler", "result": expected}
            ]
        }
        filler = CompositeFiller(items)
        result = filler.extract(None, self.user)
        self.assertEqual(expected, result)

    def test_not_fit(self):
        items = {
            "fillers": [
                {"type": "mock_filler"},
                {"type": "mock_filler"}
            ]
        }
        filler = CompositeFiller(items)
        result = filler.extract(None, self.user)
        self.assertIsNone(result)