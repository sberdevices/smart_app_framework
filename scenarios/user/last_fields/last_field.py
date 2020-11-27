# coding: utf-8
import time


class LastField:
    def __init__(self, items):
        items = items or {}
        self.value = items.get("value")
        self.remove_time = items.get("remove_time")

    def set_remove_time(self, lifetime):
        if lifetime:
            self.remove_time = int(time.time()) + lifetime

    @property
    def raw(self):
        if self.value or self.remove_time:
            return {"value": self.value,
                    "remove_time": self.remove_time}
