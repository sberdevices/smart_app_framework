from unittest import TestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.field_filler_description import FirstPersonFiller


class TestFirstPersonFiller(TestCase):
    def setUp(self):
        items = {}
        self.filler = FirstPersonFiller(items)

    def test_1(self):
        expected = {"name": "иван"}

        text_preprocessing_result = Mock()
        text_preprocessing_result.person_token_values = [{"name": "иван"}]
        result = self.filler.extract(text_preprocessing_result, None)

        self.assertDictEqual(expected, result)

    def test_2(self):
        expected = {"name": "иван"}

        text_preprocessing_result = Mock()
        text_preprocessing_result.person_token_values = [{"name": "иван"}, {"name": "иван", "patronymic": "иванович"}]
        result = self.filler.extract(text_preprocessing_result, None)

        self.assertDictEqual(expected, result)

    def test_3(self):
        text_preprocessing_result = Mock()
        text_preprocessing_result.person_token_values = []

        result = self.filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)