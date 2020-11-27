from core.utils.utils import time_check, current_time_ms
from unittest import TestCase


class TestTimeCheck(TestCase):

    def test_true(self):
        time = current_time_ms()
        self.assertTrue(time_check(time, 1 * 1000))

    def test_false(self):
        time = current_time_ms() - 40 * 1000
        self.assertFalse(time_check(time, 1 * 1000))
