from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.field_filler_description import FirstPersonFiller
from smart_kit.utils.picklable_mock import PicklableMock


class TestFirstPersonFiller(IsolatedAsyncioTestCase):
    def setUp(self):
        items = {}
        self.filler = FirstPersonFiller(items)

    async def test_1(self):
        expected = {"name": "иван"}

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.person_token_values = [{"name": "иван"}]
        result = await self.filler.extract(text_preprocessing_result, None)

        self.assertDictEqual(expected, result)

    async def test_2(self):
        expected = {"name": "иван"}

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.person_token_values = [{"name": "иван"}, {"name": "иван", "patronymic": "иванович"}]
        result = await self.filler.extract(text_preprocessing_result, None)

        self.assertDictEqual(expected, result)

    async def test_3(self):
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.person_token_values = []

        result = await self.filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)