from unittest import TestCase

from core.utils.utils import convert_to_float
from core.utils.utils import get_int, get_number


class TestNumberConverter(TestCase):
    def test_1(self):
        sample = "10"
        expected = 10
        result = get_int(sample)
        self.assertEqual(expected, result)

    def test_2(self):
        sample = "-10"
        expected = -10
        result = get_int(sample)
        self.assertEqual(expected, result)

    def test_3(self):
        sample = "+10"
        expected = 10
        result = get_int(sample)
        self.assertEqual(expected, result)

    def test_4(self):
        sample = "123f"
        expected = None
        result = get_int(sample)
        self.assertEqual(expected, result)

    def test_5(self):
        sample = "99999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999"
        expected = 99999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999999
        result = get_int(sample)
        self.assertEqual(expected, result)

    def test_6(self):
        sample = "10.5"
        expected = 10.5
        result = convert_to_float(sample)
        self.assertEqual(expected, result)

    def test_7(self):
        sample = "-10.5"
        expected = -10.5
        result = convert_to_float(sample)
        self.assertEqual(expected, result)

    def test_8(self):
        sample = "nan"
        expected = None
        result = convert_to_float(sample)
        self.assertEqual(expected, result)

    def test_9(self):
        sample = "nan"
        expected = None
        result = get_number(sample)
        self.assertEqual(expected, result)

    def test_10(self):
        sample = "-10"
        expected = -10
        result = get_number(sample)
        self.assertEqual(int, type(result))
        self.assertEqual(expected, result)

    def test_11(self):
        sample = "-10.008"
        expected = -10.008
        result = get_number(sample)
        self.assertEqual(float, type(result))
        self.assertEqual(expected, result)

    def test_12(self):
        sample = "один"
        result = convert_to_float(sample)
        self.assertIsNone(result)

    def test_13(self):
        sample = "один"
        result = get_int(sample)
        self.assertIsNone(result)

    def test_14(self):
        sample = "+79211234567"
        result = get_int(sample)
        self.assertIsNone(result)
