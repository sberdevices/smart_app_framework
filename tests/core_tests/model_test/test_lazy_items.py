import unittest
from unittest.mock import Mock

from core.model.lazy_items import LazyItems


class MockFactory:
    def __init__(self, id, items):
        self.id = id
        self.items = items


class MockDescriptions:
    def __init__(self, factory, items):
        self.items = items

    def __contains__(self, key):
        return key in self.items


class LazyItemsTest(unittest.TestCase):

    def test_clear_removed_items(self):
        raw_data = {}
        user = Mock()
        description = Mock()
        factory = Mock(raw_data, description, user)
        items = {"1": "test1", "2": "test2", "3": "test3"}
        raw_description = {"1": "test1", "2": "test2"}
        descriptions = MockDescriptions(factory, raw_description)
        items = LazyItems(items, descriptions, user, factory)
        self.assertEqual(items._raw_items, raw_description)
