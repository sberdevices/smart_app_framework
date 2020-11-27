# coding: utf-8
import unittest
from core.db_adapter import memory_adapter


class AdapterTest1(unittest.TestCase):

    def test_memory_adapter_init(self):
        obj1 = memory_adapter.MemoryAdapter()
        obj2 = memory_adapter.MemoryAdapter({'try_count': 3})
        self.assertTrue(hasattr(obj1, 'open'))
        self.assertTrue(hasattr(obj2, 'open'))
        self.assertTrue(obj1.memory_storage == {})
        self.assertTrue(obj2.memory_storage == {})
        self.assertTrue(obj1.try_count == 5)  # взято из исходников
        self.assertTrue(obj2.try_count == 3)

    def test_memory_adapter_connect(self):
        obj = memory_adapter.MemoryAdapter()
        self.assertTrue(hasattr(obj, 'connect'))

    def test_memory_adapter_open(self):
        obj = memory_adapter.MemoryAdapter()
        self.assertTrue(hasattr(obj, '_open'))
        with self.assertRaises(TypeError):
            obj._open()

    def test_memory_adapter_save(self):
        obj1 = memory_adapter.MemoryAdapter()
        obj2 = memory_adapter.MemoryAdapter()
        obj1._save(10, {'any_data'})
        obj1._save(11, {'any_data'})
        obj2._save(10, {'any_data'})
        self.assertTrue(obj1.memory_storage == {10: {'any_data'}, 11: {'any_data'}})
        self.assertTrue(obj2.memory_storage == {10: {'any_data'}})
        # метод переписывает значения
        obj2._save(10, 'any_data')
        self.assertTrue(obj2.memory_storage == {10: 'any_data'})

    def test_memory_adapter_get(self):
        obj1 = memory_adapter.MemoryAdapter()
        obj1._save(10, {'any_data'})
        obj1._save(11, 'any_data')
        self.assertTrue(obj1._get(10) == {'any_data'})
        self.assertTrue(obj1._get(11) == 'any_data')
        self.assertIsNone(obj1._get(12))

    def test_memory_adapter_list_dir(self):
        obj = memory_adapter.MemoryAdapter()
        self.assertTrue(hasattr(obj, '_list_dir'))
        with self.assertRaises(TypeError):
            obj._open()
