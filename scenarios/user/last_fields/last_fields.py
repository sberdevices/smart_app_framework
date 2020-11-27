# coding: utf-8
import time

from scenarios.user.last_fields.last_field import LastField


class LastFields:
    def __init__(self, items, user):
        self._raw_items = items or {}
        self._items = dict()
        self._factory = LastField

    def __getitem__(self, id):
        existed_item = self._items.get(id)
        if existed_item is None:
            raw_data = self._raw_items.get(id)
            existed_item = self._factory(raw_data)
            self._items[id] = existed_item
        return existed_item

    def __setitem__(self, id, value):
        self._items[id] = value

    def __iter__(self):
        return iter(self.raw)

    def expire(self):
        items = list(self.raw.keys())
        for key in items:
            item = self.raw[key]
            remove_time = item.get("remove_time")
            if remove_time and remove_time <= int(time.time()):
                self.remove(key)

    def remove(self, key):
        if key in self._raw_items:
            self._raw_items.pop(key)
        if key in self._items:
            del self._items[key]

    def clear_all(self):
        self._raw_items.clear()
        self._items.clear()

    @property
    def raw(self):
        for i in self._items:
            item = self._items[i]
            value = getattr(item, "raw", item)
            if value:
                self._raw_items[i] = value
            else:
                if i in self._raw_items:
                    self._raw_items.pop(i)
        return self._raw_items
