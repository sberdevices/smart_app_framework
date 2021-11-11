from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.field_filler_description import FirstOrgFiller


class TestFirstOrgFiller(IsolatedAsyncioTestCase):
    def setUp(self):
        items = {}
        self.filler = FirstOrgFiller(items)

    async def test_1(self):
        expected = "тинькофф"

        text_preprocessing_result = Mock()
        text_preprocessing_result.org_token_values = ["тинькофф"]
        result = await self.filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    async def test_2(self):
        expected = "тинькофф"

        text_preprocessing_result = Mock()
        text_preprocessing_result.org_token_values = ["тинькофф", "втб", "мегафон"]
        result = await self.filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    async def test_3(self):
        text_preprocessing_result = Mock()
        text_preprocessing_result.org_token_values = []

        result = await self.filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)
