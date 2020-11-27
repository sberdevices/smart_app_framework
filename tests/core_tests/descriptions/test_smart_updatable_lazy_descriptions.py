import unittest

from core.descriptions.smart_updatable_lazy_descriptions import SmartUpdatableLazyDescriptions


class MockFactory:
    def __init__(self, id, items):
        self.id = id
        self.data = items["data"]
        self.version = items["version"]


class SmartUpdatableLazyDescriptionsTest(unittest.TestCase):
    def setUp(self):
        self.descr = SmartUpdatableLazyDescriptions(MockFactory, dict(id1={"data": "raw_data_value1", "version": 0},
                                                                      id2={"data": "raw_data_value2", "version": 0}))

    def test_update_data1(self):
        update_item = dict(id1={"data": "raw_data_value3", "version": 1})
        self.descr.update_data(update_item)
        expected = "raw_data_value3"
        obj1 = self.descr["id1"]
        self.assertEqual(obj1.data, expected)
