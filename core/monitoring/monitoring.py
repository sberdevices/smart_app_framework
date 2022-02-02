# coding: utf-8
import re
from typing import Dict, Any

from prometheus_client import Counter, Histogram

COUNTER = "counter"
HISTOGRAM = "histogram"


class MonitoringBase:
    """
    Abstract adapter for monitoring
    """

    def get_counter(self, monitoring_items: Dict[str, Any], name: str, description: str = None, labels=()):
        pass

    def got_counter(self, monitoring_items: Dict[str, Any], name: str, description: str = None, labels=()):
        pass

    def got_histogram(self, monitoring_items: Dict[str, Any], name, description: str = None, buckets=()):
        pass

    def got_histogram_observe(self, monitoring_items: Dict[str, Any], name, value, description: str = None):
        pass


class MonitoringAdapterProm(MonitoringBase):
    def get_counter(self, monitoring_items: Dict[str, Any], name: str, description: str = None, labels=()):
        counter = monitoring_items[COUNTER]
        if not counter.get(name):
            counter[name] = Counter(name, description or name, labels)
        return counter[name]

    def got_counter(self, monitoring_items: Dict[str, Any], name: str, description: str = None, labels=()):
        counter = self.get_counter(monitoring_items, name, description, labels)
        if counter:
            counter.inc()

    def got_histogram(self, monitoring_items: Dict[str, Any], name, description: str = None, buckets=()):
        histogram = monitoring_items[HISTOGRAM]
        if not histogram.get(name):
            histogram[name] = Histogram(name, description or name, buckets=buckets)
        return histogram[name].time()

    def got_histogram_observe(self, monitoring_items: Dict[str, Any], name, value, description: str = None, buckets=()):
        histogram = monitoring_items[HISTOGRAM]
        if not histogram.get(name):
            histogram[name] = Histogram(name, description or name, buckets=buckets)
        return histogram[name].observe(value)


class MonitoringAdapterUFS(MonitoringBase):
    def get_counter(self, monitoring_items: Dict[str, Any], name: str, description: str = None, labels=()):
        super().get_counter(monitoring_items, name, description, labels)

    def got_counter(self, monitoring_items: Dict[str, Any], name: str, description: str = None, labels=()):
        super().got_counter(monitoring_items, name, description, labels)

    def got_histogram(self, monitoring_items: Dict[str, Any], name, description: str = None, buckets=()):
        super().got_histogram(monitoring_items, name, description, buckets)

    def got_histogram_observe(self, monitoring_items: Dict[str, Any], name, value, description: str = None):
        super().got_histogram_observe(monitoring_items, name, value, description)


class MonitoringProxy:
    COUNTER = COUNTER
    HISTOGRAM = HISTOGRAM
    DEFAULT_ENABLED = True
    DEFAULT_DISABLED_METRICS = []
    DEFAULT_ADAPTER = MonitoringAdapterProm

    def __init__(self):
        self._enabled = self.DEFAULT_ENABLED
        self._monitoring_items = {
            self.COUNTER: {},
            self.HISTOGRAM: {}
        }
        self.disabled_metrics = self.DEFAULT_DISABLED_METRICS.copy()
        self.buckets = Histogram.DEFAULT_BUCKETS
        self._adapter = self.DEFAULT_ADAPTER()

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
        self._adapter.get_counter(self._monitoring_items, name, description, labels)

    def got_counter(self, name):
        self._adapter.got_counter(self._monitoring_items, name)

    def got_histogram_decorate(self, name, description=None):
        def decor(func):
            def wrap(*args, **kwargs):
                decor_ = self.got_histogram(name, description)
                if decor_:
                    return decor_(func)(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            return wrap

        return decor

    def got_histogram(self, name, description=None):
        if not self.check_enabled(name):
            return None
        return self._adapter.got_histogram(self._monitoring_items, name, description, buckets=self.buckets)

    def got_histogram_observe(self, name, value, description=None):
        if not self.check_enabled(name):
            return None
        return self._adapter.got_histogram_observe(self._monitoring_items, name, value, buckets=self.buckets)

    def apply_config(self, config):
        self._enabled = config.get("enabled", self.DEFAULT_ENABLED)
        self.disabled_metrics = config.get("disabled_metrics", self.DEFAULT_DISABLED_METRICS.copy())
        self.buckets = config.get("buckets", Histogram.DEFAULT_BUCKETS)

    def apply_adapter(self, adapter: MonitoringBase):
        self._adapter = adapter


monitoring = MonitoringProxy()
monitoring.apply_adapter(MonitoringAdapterProm())
