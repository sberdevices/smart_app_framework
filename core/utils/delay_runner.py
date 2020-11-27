import random
from time import time


class DelayRunner:
    def __init__(self, max_delay_minutes):
        self.max_update_delay = max_delay_minutes * 60
        self._ts = 0
        self._run_item = None
        self._run_args = None

    def schedule_run(self, run_item, run_args):
        self._ts = time() + random.randint(0, self.max_update_delay)
        self._run_item = run_item
        self._run_args = run_args

    def check_can_run(self):
        return self._ts != 0 and time() >= self._ts

    def run(self):
        self._run_item(*self._run_args)
        self._clean()

    def _clean(self):
        self._ts = 0
        self._run_item = None
        self._run_args = None

