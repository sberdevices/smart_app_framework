# coding: utf-8
import unittest
from time import time

from core.basic_models.counter.counter import Counter
from core.basic_models.counter.counters import Counters


class CounterTest(unittest.TestCase):

    def _create_counter(self, value, lifetime=None, time_shift=0):
        current_time = int(time()) + time_shift
        self.items = {
            "value": value,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": lifetime
        }
        return Counter(self.items)

    def test_empty_items(self):
        counter = Counter({})
        self.assertIsNone(counter.value)
        self.assertLessEqual(counter.create_time, int(time()))
        self.assertIsNone(counter.update_time)
        self.assertIsNone(counter.lifetime)

    def test_check_expire_true(self):
        lifetime = 100
        time_shift = - (lifetime + 1)
        counter = self._create_counter(2, lifetime, time_shift)
        self.assertTrue(counter.check_expire())

    def test_check_expire_false(self):
        lifetime = 1000
        counter = self._create_counter(2, lifetime)
        self.assertFalse(counter.check_expire())

    def test_check_expire_none(self):
        counter = Counter({})
        self.assertFalse(counter.check_expire())

    def test_inc_positive(self):
        value = 2
        increment = 3
        counter = self._create_counter(value)
        counter.inc(increment)
        self.assertEqual(counter.value, (value + increment))

    def test_inc_negative(self):
        value = 3
        increment = -2
        counter = self._create_counter(value, time_shift=-10)
        counter.inc(increment)
        self.assertEqual(counter.value, value + increment)
        self.assertLess(counter.create_time, counter.update_time)

    def test_inc_from_empty(self):
        increment = 3
        items = {}
        counter = Counter(items)
        counter.inc(increment)
        self.assertEqual(counter.value, increment)
        self.assertLessEqual(counter.create_time, time())
        self.assertLessEqual(counter.update_time, time())
        self.assertIsNone(counter.lifetime)

    def test_dec(self):
        value = 3
        counter = self._create_counter(value)
        counter.dec()
        self.assertEqual(counter.value, value - 1)

    def test_dec_from_empty(self):
        items = {}
        counter = Counter(items)
        counter.dec()
        self.assertEqual(counter.value, -1)
        self.assertLessEqual(counter.create_time, time())
        self.assertLessEqual(counter.update_time, time())
        self.assertIsNone(counter.lifetime)

    def test_inc_not_create_lifetime(self):
        lifetime = 100
        counter = self._create_counter(value=0, lifetime=lifetime)
        counter.inc(lifetime=200)
        self.assertEqual(counter.lifetime, lifetime)

    def test_inc_create_lifetime(self):
        lifetime = 100
        counter = Counter({})
        counter.inc(lifetime=lifetime)
        self.assertEqual(counter.lifetime, lifetime)

    def test_set(self):
        value = 3
        new_value = 7
        counter = self._create_counter(value, time_shift=-10)
        counter.set(new_value)
        self.assertEqual(counter.value, new_value)
        self.assertLess(counter.create_time, counter.update_time)
        self.assertLessEqual(counter.update_time, time())

    def test_set_time_shift(self):
        value = 3
        new_value = 7
        time_shift = 100
        counter = self._create_counter(value)
        counter.set(new_value, time_shift=time_shift)
        self.assertEqual(counter.value, new_value)
        self.assertGreaterEqual(counter.update_time - int(time()), time_shift)

    def test_set_reset_time(self):
        value = 3
        new_value = 7
        time_shift = 100
        counter = self._create_counter(value)
        counter.set(new_value, reset_time=True)
        self.assertEqual(counter.value, new_value, time_shift)
        self.assertEqual(counter.create_time, counter.update_time)

    def test_raw(self):
        counter = self._create_counter(2)
        self.assertDictEqual(counter.raw, self.items)

    def test_eq(self):
        value = 3
        counter = self._create_counter(value)
        self.assertTrue(counter == value)

    def test_not_eq_empty_counter(self):
        value = 3
        counter = Counter({})
        self.assertFalse(counter == value)

    def test_ne(self):
        value = 3
        counter = self._create_counter(value)
        self.assertTrue(counter != 4)

    def test_lt(self):
        value = 3
        counter = self._create_counter(value)
        self.assertTrue(counter < 4)

    def test_lt_empty(self):
        counter = Counter({})
        self.assertTrue(counter < 4)

    def test_gt(self):
        value = 4
        counter = self._create_counter(value)
        self.assertTrue(counter > 3)

    def test_ge(self):
        value = 4
        counter = self._create_counter(value)
        self.assertTrue(counter >= 3)

    def test_le(self):
        value = 3
        counter = self._create_counter(value)
        self.assertTrue(counter <= 4)


class CountersTest(unittest.TestCase):

    def test_get_not_exist(self):
        name = "test_counter"
        counters = Counters({}, None)
        counter = counters.get(name)
        self.assertIsNone(counter.raw)
        self.assertEqual(counter.value, None)
        self.assertEqual(counter.create_time, int(time()))
        self.assertEqual(counter.update_time, None)
        self.assertEqual(counter.lifetime, None)

    def test_get_from_raw_items(self):
        current_time = int(time())
        name = "test_counter"
        raw_data = {name: {
            "value": 5,
            "create_time": current_time,
            "update_time": current_time
        }}
        counters = Counters(raw_data, None)
        counter = counters.get(name)
        self.assertEqual(counter.value, 5)
        self.assertEqual(counter.create_time, current_time)
        self.assertEqual(counter.update_time, current_time)
        self.assertEqual(counters.raw.get(name)["value"], 5)

    def test_get_exist(self):
        current_time = int(time())
        name = "test_counter"
        counter_data = {
            "value": 5,
            "create_time": current_time,
            "update_time": current_time
        }
        counters = Counters({}, None)
        test_counter = Counter(counter_data)
        counters._items[name] = test_counter
        counter = counters.get(name)
        self.assertEqual(counter.value, 5)
        self.assertEqual(counters.raw.get(name)["value"], 5)

    def test_raw(self):
        time_shift = 100
        current_time = int(time())
        counter_1 = {
            "value": 1,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": None
        }
        current_time = current_time + time_shift
        counter_2 = {
            "value": 2,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": None
        }
        name_1 = "test_counter_1"
        name_2 = "test_counter_2"
        counters = Counters({}, None)
        test_counter_1 = Counter(counter_1)
        test_counter_2 = Counter(counter_2)
        counters._items[name_1] = test_counter_1
        counters._items[name_2] = test_counter_2
        self.assertDictEqual(counters.raw, { name_1: counter_1, name_2: counter_2})

    def test_clear(self):
        time_shift = 100
        current_time = int(time())
        counter_1 = {
            "value": 1,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": None
        }
        current_time = current_time + time_shift
        counter_2 = {
            "value": 2,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": None
        }
        name_1 = "test_counter_1"
        name_2 = "test_counter_2"
        counters = Counters({name_1: counter_1, name_2: counter_2}, None)
        counters.clear(name_2)
        self.assertDictEqual(counters.raw, {name_1: counter_1})

    def test_clear_not_exist(self):
        current_time = int(time())
        counter_1 = {
            "value": 1,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": None
        }
        name_1 = "test_counter_1"
        name_2 = "test_counter_2"
        counters = Counters({name_1: counter_1}, None)
        counters.clear(name_2)
        self.assertDictEqual(counters.raw, {name_1: counter_1})

    def test_expire_some(self):
        lifetime = 100
        current_time = int(time())
        counter_1 = {
            "value": 1,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": lifetime
        }
        current_time = current_time - lifetime - 1
        counter_2 = {
            "value": 2,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": lifetime
        }
        name_1 = "test_counter_1"
        name_2 = "test_counter_2"
        counters = Counters({name_1: counter_1, name_2: counter_2}, None)
        counters.expire()
        self.assertDictEqual(counters.raw, {name_1: counter_1})

    def test_expire_all(self):
        lifetime = 100
        current_time = int(time()) - lifetime - 1
        counter_1 = {
            "value": 1,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": lifetime
        }

        counter_2 = {
            "value": 2,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": lifetime - 20
        }
        name_1 = "test_counter_1"
        name_2 = "test_counter_2"
        counters = Counters({name_1: counter_1, name_2: counter_2}, None)
        counters.expire()
        self.assertDictEqual(counters.raw, {})

    def test_expire_none(self):
        lifetime = 1000
        current_time = int(time())
        counter_1 = {
            "value": 1,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": lifetime
        }
        counter_2 = {
            "value": 2,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": lifetime
        }
        name_1 = "test_counter_1"
        name_2 = "test_counter_2"
        counters = Counters({name_1: counter_1, name_2: counter_2}, None)
        counters.expire()
        self.assertDictEqual(counters.raw, {name_1: counter_1, name_2: counter_2})

    def test_expire_not_set(self):
        current_time = int(time()) - 1
        counter_1 = {
            "value": 1,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": None
        }
        counter_2 = {
            "value": 2,
            "create_time": current_time,
            "update_time": current_time,
            "lifetime": None
        }
        name_1 = "test_counter_1"
        name_2 = "test_counter_2"
        counters = Counters({name_1: counter_1, name_2: counter_2}, None)
        counters.expire()
        self.assertDictEqual(counters.raw, {name_1: counter_1, name_2: counter_2})
