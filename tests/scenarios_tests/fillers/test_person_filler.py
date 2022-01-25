from unittest import TestCase

from scenarios.scenario_models.field.field_filler_description import FirstPersonFiller
from smart_kit.utils.picklable_mock import PicklableMock


class TestFirstPersonFiller(TestCase):
    def setUp(self):
        items = {}
        self.filler = FirstPersonFiller(items)

    def test_1(self):
        expected = {"name": "иван"}

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.person_token_values = [{"name": "иван"}]
        result = self.filler.extract(text_preprocessing_result, None)

        self.assertDictEqual(expected, result)

    def test_2(self):
        expected = {"name": "иван"}

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.person_token_values = [{"name": "иван"}, {"name": "иван", "patronymic": "иванович"}]
        result = self.filler.extract(text_preprocessing_result, None)

        self.assertDictEqual(expected, result)

    def test_3(self):
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.person_token_values = []

        result = self.filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)