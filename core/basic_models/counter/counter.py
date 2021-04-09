from time import time


class Counter:

    def __init__(self, items):
        items = items or {}
        self.create_time = items.get("create_time") or int(time())
        self.update_time = items.get("update_time")
        self.lifetime = items.get("lifetime")
        self.value = items.get("value")

    def check_expire(self):
        return time() - self.create_time > self.lifetime if self.lifetime else False

    def inc(self, value=1, lifetime=None):
        self._update(value, lifetime)

    def dec(self, value=-1, lifetime=None):
        self._update(value, lifetime)

    def _update(self, value, lifetime):
        self.value = self.value or 0
        self.value += value
        self.update_time = int(time())
        if self.lifetime is None:
            self.lifetime = lifetime

    def set(self, value=None, reset_time=False, time_shift=0):
        new_value = value if value is not None else self.value
        self._set(new_value, reset_time, time_shift)

    def _set(self, value, reset_time=False, time_shift=0):
        self.value = value
        self.update_time = int(time()) + time_shift
        if reset_time:
            self.create_time = self.update_time

    def __eq__(self, amount):
        value = self._get_eq_value(amount)
        return value == amount

    def __ne__(self, amount):
        value = self._get_eq_value(amount)
        return value != amount

    def __lt__(self, amount):
        value = self._get_eq_value(amount)
        return value < amount

    def __gt__(self, amount):
        value = self._get_eq_value(amount)
        return value > amount

    def __le__(self, amount):
        value = self._get_eq_value(amount)
        return value <= amount

    def __ge__(self, amount):
        value = self._get_eq_value(amount)
        return value >= amount

    def _get_eq_value(self, amount):
        if amount is None:
            value = self.value
        else:
            value = self.value or 0
        return value

    @property
    def raw(self):
        if self.value is not None:
            return {
                "value": self.value,
                "create_time": self.create_time,
                "update_time": self.update_time,
                "lifetime": self.lifetime
            }
