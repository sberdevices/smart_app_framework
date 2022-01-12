from unittest import TestCase

from scenarios.scenario_models.field.field_filler_description import FirstOrgFiller
from smart_kit.utils.picklable_mock import PicklableMock


class TestFirstOrgFiller(TestCase):
    def setUp(self):
        items = {}
        self.filler = FirstOrgFiller(items)

    def test_1(self):
        expected = "тинькофф"

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.org_token_values = ["тинькофф"]
        result = self.filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    def test_2(self):
        expected = "тинькофф"

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.org_token_values = ["тинькофф", "втб", "мегафон"]
        result = self.filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    def test_3(self):
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.org_token_values = []

        result = self.filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)
