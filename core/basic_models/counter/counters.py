# coding: utf-8
from typing import Dict

from core.basic_models.counter.counter import Counter


class Counters:

    def __init__(self, items: Dict[str, Dict], user):
        self._raw_items = items or {}
        self._items: Dict[str, Counter] = {}
        self._item_type = Counter

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key):
        counter = self._items.get(key)
        if counter is None:
            raw_data = self._raw_items.get(key)
            counter = self._item_type(raw_data)
            self._items[key] = counter
        return counter

    def clear(self, key):
        if key in self._items:
            del self._items[key]
        if key in self._raw_items:
            self._raw_items.pop(key)

    def expire(self):
        items = list(self.raw.keys())
        for key in items:
            if self[key].check_expire():
                self.clear(key)

    @property
    def raw(self):
        for name in self._items:
            counter = self._items[name]
            value = counter.raw
            if value:
                self._raw_items[name] = value
            else:
                if name in self._raw_items:
                    self._raw_items.pop(name)
        return self._raw_items
