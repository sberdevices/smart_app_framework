# coding: utf-8
from prometheus_client import Counter, Histogram


class Monitoring:
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    DEFAULT_ENABLED = True

    def __init__(self):
        self._enabled = self.DEFAULT_ENABLED
        self._monitoring_items = {
            self.COUNTER: {},
            self.HISTOGRAM: {}
        }
        self.disabled_metrics = []

    def check_enabled(self, name: str):
        metric_disabled = next((True for m in self.disabled_metrics if name.startswith(m)), False)
        return self._enabled and not metric_disabled

    def turn_on(self):
        self._enabled = True

    def turn_off(self):
        self._enabled = False

    def got_counter(self, name):
        if self.check_enabled(name):
            counter = self._monitoring_items[self.COUNTER]
            if not counter.get(name):
                counter[name] = Counter(name, name)
            counter[name].inc()

    def got_histogram(self, name):
        def decor(func):
            def wrap(*args, **kwargs):
                decor_ = self._got_histogram(name)
                if decor_:
                    return decor_(func)(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            return wrap
        return decor

    def _got_histogram(self, name):
        if self.check_enabled(name):
            histogram = self._monitoring_items[self.HISTOGRAM]
            if not histogram.get(name):
                histogram[name] = Histogram(name, name)
            return histogram[name].time()

    def got_histogram_observe(self, name, value):
        if self.check_enabled(name):
            histogram = self._monitoring_items[self.HISTOGRAM]
            if not histogram.get(name):
                histogram[name] = Histogram(name, name)
            return histogram[name].observe(value)

    def apply_config(self, config):
        self._enabled = config.get("enabled", self.DEFAULT_ENABLED)
        self.disabled_metrics = config.get("disabled_metrics", [])


monitoring = Monitoring()
