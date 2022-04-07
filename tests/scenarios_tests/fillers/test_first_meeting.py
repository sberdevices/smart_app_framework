from unittest import IsolatedAsyncioTestCase
from scenarios.scenario_models.field.field_filler_description import FirstNumberFiller, \
    FirstCurrencyFiller
from smart_kit.utils.picklable_mock import PicklableMock


class TestFirstNumberFiller(IsolatedAsyncioTestCase):
    async def test_1(self):
        expected = "5"
        items = {}
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.num_token_values = [expected]

        filler = FirstNumberFiller(items)
        result = await filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    async def test_2(self):
        items = {}
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.num_token_values = []

        filler = FirstNumberFiller(items)
        result = await filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)


class TestFirstCurrencyFiller(IsolatedAsyncioTestCase):
    async def test_1(self):
        expected = "ru"
        items = {}
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.ccy_token_values = [expected]

        filler = FirstCurrencyFiller(items)
        result = await filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    async def test_2(self):
        items = {}
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.ccy_token_values = []

        filler = FirstCurrencyFiller(items)
        result = await filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)
