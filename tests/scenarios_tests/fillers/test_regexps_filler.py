from unittest import IsolatedAsyncioTestCase

from scenarios.scenario_models.field.field_filler_description import AllRegexpsFieldFiller
from smart_kit.utils.picklable_mock import PicklableMock


class Test_regexps_filler(IsolatedAsyncioTestCase):
    def setUp(self):
        self.items = {}
        self.items["exps"] = ["номер[а-я]*\.?\s?(\d+)", "n\.?\s?(\d+)", "nn\.?\s?(\d+)", "#\.?\s?(\d+)",
                             "##\.?\s?(\d+)",
                             "№\.?\s?(\d+)", "№№\.?\s?(\d+)", "платеж[а-я]+\.?\s?(\d+)", "поручен[а-я]+\.?\s?(\d+)",
                             "п\\s?,\\s?п\.?\s?(\d+)", "п\\s?\\/\\s?п\.?\s?(\d+)"]
        self.items["delimiter"] = "|"

        self.filler = AllRegexpsFieldFiller(self.items)

    async def test_extract_1(self):
        field_value = "Просим отозвать платежное поручение 14 от 23.01.19 на сумму 3500 и вернуть деньги на расчетный счет."
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.original_text = field_value

        filler = AllRegexpsFieldFiller(self.items)
        result = await filler.extract(text_preprocessing_result, None)
        self.assertEqual('14', result)

    async def test_extract_2(self):
        field_value = "поручение12 поручение14 #1 n3 п/п70 n33"
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.original_text = field_value

        filler = AllRegexpsFieldFiller(self.items)
        result = await filler.extract(text_preprocessing_result, None)
        self.assertEqual("3|33|1|12|14|70", result)

    async def test_extract_no_match(self):
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.original_text = "текст без искомых номеров"

        filler = AllRegexpsFieldFiller(self.items)
        result = await filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)
