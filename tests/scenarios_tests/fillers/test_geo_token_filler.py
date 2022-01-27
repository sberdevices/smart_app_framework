from unittest import TestCase

from scenarios.scenario_models.field.field_filler_description import FirstGeoFiller
from smart_kit.utils.picklable_mock import PicklableMock


class TestFirstGeoFiller(TestCase):
    def setUp(self):
        items = {}
        self.filler = FirstGeoFiller(items)

    def test_1(self):
        expected = "москва"

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.geo_token_values = ["москва"]
        result = self.filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    def test_2(self):
        expected = "москва"

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.geo_token_values = ["москва", "питер", "казань"]
        result = self.filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    def test_3(self):
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.geo_token_values = []

        result = self.filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)
