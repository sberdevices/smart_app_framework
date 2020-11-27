# coding: utf-8
import unittest

from core.basic_models.operators.comparators import MoreComparator, \
    LessComparator, MoreOrEqualComparator, LessOrEqualComparator, EqualComparator


class ComparatorsTest(unittest.TestCase):
    def test_more_compare_sucsess(self):
        comparator = MoreComparator({})
        assert comparator.compare(3, 1)

    def test_more_compare_fail(self):
        comparator = MoreComparator({})
        assert not comparator.compare(3, 10)

    def test_less_compare_sucsess(self):
        comparator = LessComparator({})
        assert comparator.compare(3, 10)

    def test_less_compare_fail(self):
        comparator = LessComparator({})
        assert not comparator.compare(3, 1)

    def test_more_or_equal_sucsess(self):
        comparator = MoreOrEqualComparator({})
        assert comparator.compare(1, 1)

    def test_more_or_equal_fail(self):
        comparator = MoreOrEqualComparator({})
        assert not comparator.compare(1, 3)

    def test_less_or_equal_sucsess(self):
        comparator = LessOrEqualComparator({})
        assert comparator.compare(1, 1)

    def test_less_or_equal_fail(self):
        comparator = LessOrEqualComparator({})
        assert not comparator.compare(3, 1)

    def test_equal_sucsess(self):
        comparator = EqualComparator({})
        assert comparator.compare(1, 1)

    def test_equal_fail(self):
        comparator = EqualComparator({})
        assert not comparator.compare(1, 2)


if __name__ == '__main__':
    unittest.main()
