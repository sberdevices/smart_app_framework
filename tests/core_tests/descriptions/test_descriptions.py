import unittest

from core.descriptions.descriptions import Descriptions, registered_description_factories, default_description_factory
from core.repositories.base_repository import BaseRepository


class MockDescription1:
    def __init__(self, raw_data):
        self.raw_data = raw_data

    @property
    def raw(self):
        return self.raw_data


class MockDescription2(MockDescription1):
    pass


class MockRepository(BaseRepository):
    def __init__(self, data, key):
        super(MockRepository, self).__init__(key=key)
        self.data = data


class DescriptionsTest(unittest.TestCase):
    def setUp(self):
        val1 = MockRepository("raw_1", "repo_key1")
        val2 = MockRepository("raw_2", "repo_key2")
        val3 = MockRepository("raw_3", "repo_key3")
        self.registered_repos = {"repo_key1": val1, "repo_key2": val2, "repo_key3": val3}
        registered_description_factories[self.registered_repos["repo_key1"].key] = MockDescription1
        registered_description_factories[self.registered_repos["repo_key2"].key] = MockDescription2
        registered_description_factories[self.registered_repos["repo_key3"].key] = default_description_factory
        self.descriptions = Descriptions(registered_repositories=self.registered_repos)

    def test_get1(self):
        item1 = self.descriptions["repo_key1"]
        assert item1.raw == "raw_1"
        assert type(item1) == MockDescription1

    def test_get2(self):
        item2 = self.descriptions["repo_key2"]
        assert item2.raw == "raw_2"
        assert type(item2) == MockDescription2

    def test_get3(self):
        item2 = self.descriptions["repo_key3"]
        assert item2 == "raw_3"


if __name__ == '__main__':
    unittest.main()
