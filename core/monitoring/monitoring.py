# coding: utf-8
import re

from prometheus_client import Counter, Histogram


class Monitoring:
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    DEFAULT_ENABLED = True
    DEFAULT_DISABLED_METRICS = []

    def __init__(self):
        self._enabled = self.DEFAULT_ENABLED
        self._monitoring_items = {
            self.COUNTER: {},
            self.HISTOGRAM: {}
        }
        self.disabled_metrics = self.DEFAULT_DISABLED_METRICS.copy()
        self.buckets = Histogram.DEFAULT_BUCKETS

    def check_enabled(self, name: str):
        metric_disabled = next((True for m in self.disabled_metrics if re.fullmatch(m, name)), False)
        return self._enabled and not metric_disabled

    def turn_on(self):
        self._enabled = True

    def turn_off(self):
        self._enabled = False

    def get_counter(self, name, description=None, labels=()):
        if not self.check_enabled(name):
            return None
        counter = self._monitoring_items[self.COUNTER]
        if not counter.get(name):
            counter[name] = Counter(name, description or name, labels)
        return counter[name]

    def got_counter(self, name, description=None, labels=()):
        counter = self.get_counter(name, description, labels)
        if counter:
            counter.inc()

    def got_histogram_decorate(self, name, description=None):
        def decor(func):
            def wrap(*args, **kwargs):
                decor_ = self.got_histogram(name, description=None)
                if decor_:
                    return decor_(func)(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            return wrap
        return decor

    def got_histogram(self, name, description=None):
        if self.check_enabled(name):
            histogram = self._monitoring_items[self.HISTOGRAM]
            if not histogram.get(name):
                histogram[name] = Histogram(name, description or name, buckets=self.buckets)
            return histogram[name].time()

    def got_histogram_observe(self, name, value, description=None):
        if self.check_enabled(name):
            histogram = self._monitoring_items[self.HISTOGRAM]
            if not histogram.get(name):
                histogram[name] = Histogram(name, description or name, buckets=self.buckets)
            return histogram[name].observe(value)

    def apply_config(self, config):
        self._enabled = config.get("enabled", self.DEFAULT_ENABLED)
        self.disabled_metrics = config.get("disabled_metrics", self.DEFAULT_DISABLED_METRICS.copy())
        self.buckets = config.get("buckets", Histogram.DEFAULT_BUCKETS)


monitoring = Monitoring()
