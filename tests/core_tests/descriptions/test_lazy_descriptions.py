import unittest

from core.descriptions.descriptions_items import DescriptionsItems


class MockFactory():
    def __init__(self, id, items):
        self.id = id
        self.items = items
        self.custom_value = None

    def set_custom_value(self, value):
        self.custom_value = value


class DescriptionsTest(unittest.TestCase):
    def setUp(self):
        self.descr = DescriptionsItems(MockFactory, dict(id1=["raw_data_value1"], id2=["raw_data_value2"]))

    def test_getitem(self):
        obj1 = self.descr["id1"]
        assert obj1.items == ["raw_data_value1"]
        obj1.set_custom_value(1)
        obj2 = self.descr["id1"]
        assert obj2 == obj1

    def test_len(self):
        assert len(self.descr) == 2

    def test_iter(self):
        cnt = 0
        items = []
        for item in self.descr:
            cnt += 1
            items += self.descr[item].items
        assert cnt == 2 and set(items) == {"raw_data_value1", "raw_data_value2"}

    def test_get_keys(self):
        assert set(self.descr.get_keys()) == {"id1", "id2"}

    def test_has_key(self):
        assert "id1" in self.descr
        assert not "invalid" in self.descr

    def test_update_data(self):
        items = dict(id1=["raw_data_value11"], id3=["raw_data_value3"])
        expected = items
        self.descr.update_data(items)
        self.assertEqual(len(self.descr._items), 2)
        self.assertEqual(set(self.descr._raw_items), set(expected))

    def test_update_item(self):
        id = "id1"
        expected = "raw_data_value11"
        print(self.descr._raw_items)
        self.descr.update_item(id, expected)
        self.assertEqual(self.descr._raw_items[id], expected)

    def test_remove_item(self):
        id = "id1"
        self.descr.remove_item(id)
        self.assertIsNone(self.descr._items.get(id))
        self.assertIsNone(self.descr._raw_items.get(id))