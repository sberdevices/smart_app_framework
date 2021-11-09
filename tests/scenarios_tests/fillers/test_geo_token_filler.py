from unittest import TestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.field_filler_description import FirstGeoFiller


class TestFirstGeoFiller(TestCase):
    def setUp(self):
        items = {}
        self.filler = FirstGeoFiller(items)

    async def test_1(self):
        expected = "москва"

        text_preprocessing_result = Mock()
        text_preprocessing_result.geo_token_values = ["москва"]
        result = await self.filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    async def test_2(self):
        expected = "москва"

        text_preprocessing_result = Mock()
        text_preprocessing_result.geo_token_values = ["москва", "питер", "казань"]
        result = await self.filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    async def test_3(self):
        text_preprocessing_result = Mock()
        text_preprocessing_result.geo_token_values = []

        result = await self.filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)
