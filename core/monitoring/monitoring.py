# coding: utf-8
from prometheus_client import Counter, Histogram


class Monitoring:
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    DEFAULT_ENABLED = True

    def __init__(self):
        self._enabled = self.DEFAULT_ENABLED
        self._monitoring_items = {self.COUNTER: {},
                                  self.HISTOGRAM: {}
                                  }

    def check_enabled(self):
        return self._enabled

    def turn_on(self):
        self._enabled = True

    def turn_off(self):
        self._enabled = False

    def got_counter(self, name):
        if self.check_enabled():
            counter = self._monitoring_items[self.COUNTER]
            if not counter.get(name):
                counter[name] = Counter(name, name)
            counter[name].inc()

    def got_histogram(self, name):
        if self.check_enabled():
            histogram = self._monitoring_items[self.HISTOGRAM]
            if not histogram.get(name):
                histogram[name] = Histogram(name, name)
            return histogram[name].time()

    def got_histogram_observe(self, name, value):
        if self.check_enabled():
            histogram = self._monitoring_items[self.HISTOGRAM]
            if not histogram.get(name):
                histogram[name] = Histogram(name, name)
            return histogram[name].observe(value)


monitoring = Monitoring()
