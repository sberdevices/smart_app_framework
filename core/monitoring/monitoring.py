# coding: utf-8
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, Any, Union, Callable
from time import time

import aiohttp
import requests
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


class MonitoringAdapterUFS(MonitoringBase):
    DEFAULT_URL = ""

    def __init__(self):
        self._monitoring_items = {
            COUNTER: defaultdict(int),
            HISTOGRAM: defaultdict(list)
        }
        self._url = self.DEFAULT_URL

    def get_counter(self, name: str, description: str = None, labels=()):
        counter: defaultdict[Any, int] = self._monitoring_items[COUNTER]
        return counter[name]

    def got_counter(self, name: str, description: str = None, labels=()):
        counter: defaultdict[Any, int] = self._monitoring_items[COUNTER]
        counter[name] += 1

    def got_histogram(self, name: str, description: str = None, buckets=()):
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time()
                ret = func(*args, **kwargs)
                end = time()

                histogram: defaultdict[Any, list] = self._monitoring_items[HISTOGRAM]
                histogram[name].append(end - start)

                return ret
            return wrapper
        return decorator

    def got_histogram_observe(self, name, value, description: str = None, buckets=()):
        histogram: defaultdict[Any, list] = self._monitoring_items[HISTOGRAM]
        histogram[name].append(value)

    def apply_config(self, config: dict):
        self._url = config.get("enabled", self.DEFAULT_URL)

    def send(self):
        metrics = [{'metric': name, 'type': COUNTER, 'value': [value]} for name, value in self._monitoring_items[COUNTER].items()] + \
                  [{'metric': name, 'type': HISTOGRAM, 'value': value} for name, value in self._monitoring_items[HISTOGRAM].items()]
        # requests now, aiohttp needs tests on async kafka
        requests.post("http://ptsv2.com/t/tkw9y-1644243206/post", json={'metrics': metrics})


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

    @property
    def _monitoring_items(self):
        return self._adapter._monitoring_items


monitoring = MonitoringProxy()
monitoring.apply_adapter(MonitoringAdapterProm())
