from unittest import TestCase

import time
from unittest.mock import Mock

from core.utils.delay_runner import DelayRunner


class TestDelayRunner(TestCase):
    def setUp(self):
        self.max_delay = 1
        self.max_delay_s = self.max_delay * 60
        self.delay_runner = DelayRunner(1)
        self.run = Mock()
        self.arg = Mock()
        self.delay_runner.schedule_run(self.run, [self.arg])


    def test_set_run_time(self):
        self.assertEqual(self.delay_runner._run_item, self.run)
        self.assertListEqual(self.delay_runner._run_args, [self.arg])
        self.assertTrue(0 < self.delay_runner._ts - time.time() < self.max_delay_s)

    def test_check_can_run(self):
        self.delay_runner._ts = self.delay_runner._ts - self.max_delay_s
        self.assertTrue(self.delay_runner.check_can_run())

    def test_check_cant_run(self):
        self.delay_runner._ts = time.time() + self.max_delay_s
        self.assertFalse(self.delay_runner.check_can_run())

    def test_run(self):
        self.delay_runner._ts = self.delay_runner._ts - self.max_delay_s
        self.delay_runner.run()
        self.run.assert_called_once_with(self.arg)
        self.assertLess(self.delay_runner._ts, time.time())
        self.assertIsNone(self.delay_runner._run_args)
        self.assertIsNone(self.delay_runner._run_item)
