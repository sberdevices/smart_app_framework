# coding: utf-8
import unittest

from core.model.heapq.heapq_storage import HeapqKV
from core.model.heapq.heapq_storage import heapq

class ModelsTest2(unittest.TestCase):
    def setUp(self):
        self.test_value = 10
        self.test_key_func = lambda x: x**2

    def test_heapq_storage_init(self):
        obj = HeapqKV(self.test_key_func)
        self.assertTrue(obj._heapq == [])
        self.assertTrue(obj._to_remove == set())
        self.assertTrue(obj._value_to_key == self.test_key_func)

    def test_heapq_storage_value_to_key(self):
        obj = HeapqKV(self.test_key_func)
        self.assertTrue(obj.value_to_key(self.test_value) == 100)

    def test_heapq_storage_push(self):
        obj = HeapqKV(self.test_key_func)
        obj.push(1, 2)
        self.assertTrue(obj._heapq == [(1, 2)])
        obj.push(3, 4)
        self.assertTrue(obj._heapq == [(1, 2), (3, 4)])

    def test_heapq_storage_check_key_valid(self):
        obj = HeapqKV(self.test_key_func)
        key_val = obj.value_to_key(self.test_value)
        self.assertTrue(obj._check_key_valid(self.test_value))
        obj._to_remove.add(key_val)
        self.assertTrue(not obj._check_key_valid(self.test_value))
        self.assertTrue(obj._to_remove == set())

    def test_heapq_storage_remove(self):
        obj = HeapqKV(self.test_key_func)
        self.assertTrue(obj._to_remove == set())
        obj.remove(self.test_value)
        self.assertTrue(obj._to_remove == {self.test_value})

    def test_heapq_storage_get_head_key(self):
        # while используется как аналог bool(list)

        obj = HeapqKV(self.test_key_func)
        # проверка при выполнении условия
        obj.push(2, 4)
        self.assertTrue(obj.get_head_key() == 2)
        heapq.heappop(obj._heapq)
        obj.push(3, 9)
        self.assertTrue(obj.get_head_key() == 3)
        heapq.heappop(obj._heapq)
        # функция может ничего не возвращать
        self.assertIsNone(obj.get_head_key())

        # проверка при невыполнении условия
        obj.push(2, 4)
        obj._to_remove.add(16)  # использовалась функция вовзедения в квадрат числа 4**2 = 16
        self.assertIsNone(obj.get_head_key())
        self.assertTrue(obj._heapq == [])

    def test_heapq_storage_pop(self):
        # while используется как аналог bool(list) и не даёт возникнуть исключению IndexError для pop
        obj = HeapqKV(self.test_key_func)
        # проверка при выполнении условия с возвратом
        obj.push(2, 4)
        self.assertTrue(obj.pop() == (2, 4))
        self.assertIsNone(obj.pop())
        # проверка при невыполнении условия
        obj.push(2, 4)
        obj._to_remove.add(16)
        self.assertIsNone(obj.pop())
        self.assertTrue(obj._heapq == [])
