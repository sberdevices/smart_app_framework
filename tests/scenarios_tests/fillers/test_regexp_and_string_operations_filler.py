from unittest import TestCase 
from unittest.mock import Mock
from scenarios.scenario_models.field.field_filler_description import RegexpAndStringOperationsFieldFiller


class PickableMock(Mock):
    def __reduce__(self):
        return (Mock, ())


class TestRegexpStringOperationsFiller(TestCase):
    def setUp(self):
        self.items = {"exp": "1-[0-9A-Z]{7}"}

    def _test_operation(self, field_value, type_op, amount):
        self.items["operations"] = []
        text_preprocessing_result = PickableMock()
        text_preprocessing_result.original_text = field_value

        filler = RegexpAndStringOperationsFieldFiller(self.items)
        return filler._operation(field_value, type_op, amount)

    def test_operation(self):
        field_value = "1-RSAR09A"
        type_op = "lower"

        result = self._test_operation(field_value, type_op, None)
        self.assertEqual(field_value.lower(), result)

    def test_operation_amount(self):
        field_value = "1-RSAR09A"
        type_op = "lstrip"
        amount = "1-"

        result = self._test_operation(field_value, type_op, amount)
        self.assertEqual(field_value.lstrip(amount), result)

    def _test_extract(self, field_value):
        text_preprocessing_result = PickableMock()
        text_preprocessing_result.original_text = field_value

        filler = RegexpAndStringOperationsFieldFiller(self.items)
        return filler.extract(text_preprocessing_result, None)

    def test_extract_upper(self):
        field_value = "1-rsar09a"
        self.items["operations"] = [{"type":"upper"}]

        result = self._test_extract(field_value)
        self.assertEqual(field_value.upper(), result)

    def test_extract_rstrip(self):
        field_value = "1-RSAR09A !)"
        self.items["operations"] = [{"type":"rstrip", "amount": "!) "}]

        result = self._test_extract(field_value)
        self.assertEqual(field_value.rstrip("!) "), result)

    def test_extract_upper_rstrip(self):
        field_value = "1-rsar09a !)"
        self.items["operations"] = [ {"type":"upper"}, {"type":"rstrip", "amount": "!) "} ]

        result = self._test_extract(field_value)
        self.assertEqual(field_value.upper().rstrip("!) "), result)

    def test_extract_no_operations(self):
        field_value = "1-rsar09a !)"
        self.items["operations"] = []

        result = self._test_extract(field_value)
        self.assertIsNone(result)

