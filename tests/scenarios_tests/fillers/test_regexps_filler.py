from unittest import TestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.field_filler_description import AllRegexpsFieldFiller


class Test_regexps_filler(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = {}
        cls.items["exps"] = ["номер[а-я]*\.?\s?(\d+)", "n\.?\s?(\d+)", "nn\.?\s?(\d+)", "#\.?\s?(\d+)",
                             "##\.?\s?(\d+)",
                             "№\.?\s?(\d+)", "№№\.?\s?(\d+)", "платеж[а-я]+\.?\s?(\d+)", "поручен[а-я]+\.?\s?(\d+)",
                             "п\\s?,\\s?п\.?\s?(\d+)", "п\\s?\\/\\s?п\.?\s?(\d+)"]
        cls.items["delimiter"] = "|"

        cls.filler = AllRegexpsFieldFiller(cls.items)

    def test_extract_1(self):
        field_value = "Просим отозвать платежное поручение 14 от 23.01.19 на сумму 3500 и вернуть деньги на расчетный счет."
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = field_value

        filler = AllRegexpsFieldFiller(self.items)
        result = filler.extract(text_preprocessing_result, None)
        self.assertEqual('14', result)

    def test_extract_2(self):
        field_value = "поручение12 поручение14 #1 n3 п/п70 n33"
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = field_value

        filler = AllRegexpsFieldFiller(self.items)
        result = filler.extract(text_preprocessing_result, None)
        self.assertEqual("3|33|1|12|14|70", result)

    def test_extract_no_match(self):
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = "текст без искомых номеров"

        filler = AllRegexpsFieldFiller(self.items)
        result = filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)
