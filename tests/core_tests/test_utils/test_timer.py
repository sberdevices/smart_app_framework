from core.utils.stats_timer import StatsTimer
from unittest import TestCase


class TestStatsTimer(TestCase):

    def test_1(self):
        timer = StatsTimer()
        with timer:
            a = 3

        self.assertTrue(timer.msecs > 0)
