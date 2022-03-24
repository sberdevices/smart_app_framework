# coding: utf-8
import unittest

from core.db_adapter import memory_adapter


class AdapterTest1(unittest.IsolatedAsyncioTestCase):

    async def test_memory_adapter_init(self):
        obj1 = memory_adapter.MemoryAdapter()
        obj2 = memory_adapter.MemoryAdapter({'try_count': 3})
        self.assertTrue(hasattr(obj1, 'open'))
        self.assertTrue(hasattr(obj2, 'open'))
        self.assertEqual(obj1.memory_storage, {})
        self.assertEqual(obj2.memory_storage, {})
        self.assertEqual(obj1.try_count, 5)  # взято из исходников
        self.assertEqual(obj2.try_count, 3)

    async def test_memory_adapter_connect(self):
        obj = memory_adapter.MemoryAdapter()
        self.assertTrue(hasattr(obj, 'connect'))

    async def test_memory_adapter_open(self):
        obj = memory_adapter.MemoryAdapter()
        self.assertTrue(hasattr(obj, '_open'))
        with self.assertRaises(TypeError):
            await obj._open()

    async def test_memory_adapter_save(self):
        obj1 = memory_adapter.MemoryAdapter()
        obj2 = memory_adapter.MemoryAdapter()
        await obj1._save(10, {'any_data'})
        await obj1._save(11, {'any_data'})
        await obj2._save(10, {'any_data'})
        self.assertEqual(obj1.memory_storage, {10: {'any_data'}, 11: {'any_data'}})
        self.assertEqual(obj2.memory_storage, {10: {'any_data'}})
        # метод переписывает значения
        await obj2._save(10, 'any_data')
        self.assertEqual(obj2.memory_storage, {10: 'any_data'})

    async def test_memory_adapter_get(self):
        obj1 = memory_adapter.MemoryAdapter()
        await obj1._save(10, {'any_data'})
        await obj1._save(11, 'any_data')
        self.assertEqual(await obj1._get(10), {'any_data'})
        self.assertEqual(await obj1._get(11), 'any_data')
        self.assertIsNone(await obj1._get(12))

    async def test_memory_adapter_list_dir(self):
        obj = memory_adapter.MemoryAdapter()
        self.assertTrue(hasattr(obj, '_list_dir'))
        with self.assertRaises(TypeError):
            await obj._open()
