from unittest import TestCase
from unittest.mock import Mock
from scenarios.scenario_models.field.field_filler_description import RegexpFieldFiller


class TestRegexpFiller(TestCase):
    def setUp(self):
        self.items = {"exp": "1-[0-9A-Z]{7}"}
        self.user = Mock()
        self.user.message = Mock()
        self.user.message.masked_value = ""

    def test_no_exp_init(self):
        self.assertRaises(KeyError, RegexpFieldFiller, {})

    async def test_no_exp(self):
        field_value = "1-RSAR09A"
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = field_value

        filler = RegexpFieldFiller(self.items)
        filler.regexp = None
        self.assertIsNone(await filler.extract(text_preprocessing_result, self.user))

    async def test_extract(self):
        field_value = "1-RSAR09A"
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = field_value

        filler = RegexpFieldFiller(self.items)
        result = await filler.extract(text_preprocessing_result, self.user)

        self.assertEqual(field_value, result)

    async def test_extract_no_match(self):
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = "text"

        filler = RegexpFieldFiller(self.items)
        result = await filler.extract(text_preprocessing_result, self.user)

        self.assertIsNone(result)

    async def test_extract_mult_match_default_delimiter(self):
        field_value = "1-RSAR09A пустой тест 1-RSAR02A"
        res = ",".join(['1-RSAR09A', '1-RSAR02A'])
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = field_value

        filler = RegexpFieldFiller(self.items)
        result = await filler.extract(text_preprocessing_result, self.user)

        self.assertEqual(res, result)

    async def test_extract_mult_match_custom_delimiter(self):
        field_value = "1-RSAR09A пустой тест 1-RSAR02B"
        self.items["delimiter"] = ";"
        res = self.items["delimiter"].join(['1-RSAR09A', '1-RSAR02B'])
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = field_value

        filler = RegexpFieldFiller(self.items)
        result = await filler.extract(text_preprocessing_result, self.user)

        self.assertEqual(res, result)
