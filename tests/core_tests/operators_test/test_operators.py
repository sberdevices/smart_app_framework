# coding: utf-8
import unittest

from core.basic_models.operators.operators import MoreOperator, \
    LessOperator, MoreOrEqualOperator, LessOrEqualOperator, EqualOperator, \
    EndsWithOperator, Exists, StartsWithOperator, InOperator


class MoreOperatorTest(unittest.TestCase):
    def test_more_compare_sucsess(self):
        operator = MoreOperator({"amount": 1})
        assert operator.compare(3)

    def test_more_compare_fail(self):
        operator = MoreOperator({"amount": 10})
        assert not operator.compare(3)

    def test_less_compare_sucsess(self):
        operator = LessOperator({"amount": 10})
        assert operator.compare(3)

    def test_less_compare_fail(self):
        operator = LessOperator({"amount": 1})
        assert not operator.compare(3)

    def test_more_or_equal_sucsess(self):
        operator = MoreOrEqualOperator({"amount": 1})
        assert operator.compare(1)

    def test_more_or_equal_fail(self):
        operator = MoreOrEqualOperator({"amount": 3})
        assert not operator.compare(1)

    def test_less_or_equal_sucsess(self):
        operator = LessOrEqualOperator({"amount": 1})
        assert operator.compare(1)

    def test_less_or_equal_fail(self):
        operator = LessOrEqualOperator({"amount": 1})
        assert not operator.compare(3)

    def test_equal_sucsess(self):
        operator = EqualOperator({"amount": 1})
        assert operator.compare(1)

    def test_equal_fail(self):
        operator = EqualOperator({"amount": 2})
        assert not operator.compare(1)

    def test_in_success(self):
        operator = InOperator({"amount": ["val1", "val2"]})
        assert operator.compare("val1")

    def test_in_fail(self):
        operator = InOperator({"amount": ["val1", "val2"]})
        self.assertFalse(operator.compare("another_value"))

    def test_endswith_success_with_string(self):
        operator = EndsWithOperator({'amount': 'abcd'})
        assert operator.compare('abbbabcd')

    def test_endswith_success_with_digits(self):
        operator = EndsWithOperator({'amount': 7890})
        assert operator.compare('1234567890')

    def test_endswith_success_with_digits_2(self):
        operator = EndsWithOperator({'amount': '7890'})
        assert operator.compare(1234567890)

    def test_endswith_fail_with_string(self):
        operator = EndsWithOperator({'amount': 'abcd'})
        assert not operator.compare('abbbabcda')

    def test_endswith_fail_with_digits(self):
        operator = EndsWithOperator({'amount': 78901})
        assert not operator.compare('1234567890')

    def test_endswith_fail_with_digits_2(self):
        operator = EndsWithOperator({'amount': '78901'})
        assert not operator.compare(1234567890)

    def test_startswith_success_with_string(self):
        operator = StartsWithOperator({'amount': 'abbb'})
        assert operator.compare('abbbabcd')

    def test_startswith_success_with_digits(self):
        operator = StartsWithOperator({'amount': 1234})
        assert operator.compare('1234567890')

    def test_startswith_success_with_digits_2(self):
        operator = StartsWithOperator({'amount': '1234'})
        assert operator.compare(1234567890)

    def test_startswith_fail_with_string(self):
        operator = StartsWithOperator({'amount': 'abbc'})
        assert not operator.compare('abbbabcda')

    def test_startswith_fail_with_digits(self):
        operator = StartsWithOperator({'amount': 1233})
        assert not operator.compare('1234567890')

    def test_startswith_fail_with_digits_2(self):
        operator = StartsWithOperator({'amount': '1233'})
        assert not operator.compare(1234567890)

    def test_exists_success(self):
        operator = Exists({})
        self.assertTrue(operator.compare('value'))

    def test_exists_fail(self):
        operator = Exists({})
        self.assertFalse(operator.compare(None))


if __name__ == '__main__':
    unittest.main()
