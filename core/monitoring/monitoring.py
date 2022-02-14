# coding: utf-8
import re
from abc import ABC, abstractmethod
from typing import Dict, Any, Union, Callable

from prometheus_client import Counter, Histogram

COUNTER = "counter"
HISTOGRAM = "histogram"


class MonitoringBase(ABC):
    """
    Abstract adapter for monitoring
    """

    COUNTER = COUNTER
    HISTOGRAM = HISTOGRAM

    @abstractmethod
    def __init__(self):
        self._monitoring_items: Dict[str, Dict[str, Any]] = {}

    @abstractmethod
    def get_counter(self, name: str, description: str = None, labels=()):
        pass

    @abstractmethod
    def got_counter(self, name: str, description: str = None, labels=()):
        pass

    @abstractmethod
    def got_histogram(self, name: str, description: str = None, buckets=()) -> Callable:
        pass

    @abstractmethod
    def got_histogram_observe(self, name, value, description: str = None, buckets=()):
        pass

    def send(self):
        pass

    async def async_send(self):
        pass

    def apply_config(self, config: dict):
        pass

    def on_apply(self):
        pass


class MonitoringAdapterProm(MonitoringBase):
    def __init__(self):
        self._monitoring_items: Dict[str, Dict[str, Union[Counter, Histogram]]] = {
            COUNTER: {},
            HISTOGRAM: {}
        }
        self.buckets = Histogram.DEFAULT_BUCKETS

    def get_counter(self, name: str, description: str = None, labels=()) -> Counter:
        counter = self._monitoring_items[COUNTER]
        if not counter.get(name):
            counter[name] = Counter(name, description or name, labels)
        return counter[name]

    def got_counter(self, name: str, description: str = None, labels=()):
        counter = self.get_counter(name, description, labels)
        if counter:
            counter.inc()

    def got_histogram(self, name: str, description: str = None, buckets=()):
        if not buckets:
            buckets = self.buckets
        histogram = self._monitoring_items[HISTOGRAM]
        if not histogram.get(name):
            histogram[name] = Histogram(name, description or name, buckets=buckets)
        return histogram[name].time()

    def got_histogram_observe(self, name: str, value, description: str = None, buckets=()):
        if not buckets:
            buckets = self.buckets
        histogram = self._monitoring_items[HISTOGRAM]
        if not histogram.get(name):
            histogram[name] = Histogram(name, description or name, buckets=buckets)
        return histogram[name].observe(value)

    def apply_config(self, config: dict):
        self.buckets = config.get("buckets", Histogram.DEFAULT_BUCKETS)


class MonitoringProxy(MonitoringBase):
    DEFAULT_ENABLED = True
    DEFAULT_DISABLED_METRICS = []
    DEFAULT_ADAPTER = MonitoringAdapterProm
    _adapter = None

    def __init__(self):
        self._enabled = self.DEFAULT_ENABLED
        self.disabled_metrics = self.DEFAULT_DISABLED_METRICS.copy()
        self.apply_adapter(self.DEFAULT_ADAPTER())

    def check_enabled(self, name: str):
        metric_disabled = next((True for m in self.disabled_metrics if re.fullmatch(m, name)), False)
        return self._enabled and not metric_disabled

    def turn_on(self):
        self._enabled = True

    def turn_off(self):
        self._enabled = False

    def get_counter(self, name: str, description: str = None, labels=()):
        if not self.check_enabled(name):
            return None
        return self._adapter.get_counter(name, description, labels)

    def got_counter(self, name: str, description: str = None, labels=()):
        if not self.check_enabled(name):
            return None
        self._adapter.got_counter(name)

    def got_histogram(self, name: str, description: str = None, buckets=()):
        if not self.check_enabled(name):
            return None
        return self._adapter.got_histogram(name, description, buckets=buckets)

    def got_histogram_observe(self, name, value, description: str = None, buckets=()):
        if not self.check_enabled(name):
            return None
        return self._adapter.got_histogram_observe(name, value, description, buckets=buckets)

    # FIXME check decorator
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

    def apply_config(self, config):
        self._enabled = config.get("enabled", self.DEFAULT_ENABLED)
        self.disabled_metrics = config.get("disabled_metrics", self.DEFAULT_DISABLED_METRICS.copy())
        self._adapter.apply_config(config)

    def apply_adapter(self, adapter: MonitoringBase):
        self._adapter = adapter
        self._adapter.on_apply()

    def send(self):
        self._adapter.send()

    async def async_send(self):
        await self._adapter.async_send()

    @property
    def _monitoring_items(self):
        return self._adapter._monitoring_items


monitoring = MonitoringProxy()
monitoring.apply_adapter(MonitoringAdapterProm())
