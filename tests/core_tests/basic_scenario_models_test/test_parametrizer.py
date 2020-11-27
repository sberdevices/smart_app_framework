import unittest
from unittest.mock import Mock

from core.basic_models.parametrizers.parametrizer import BasicParametrizer


class ParametrizerTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.user = Mock(message=Mock())

    def test_get_user_data(self):
        expected = ["message"]
        parametrizer = BasicParametrizer(self.user, {})
        result = parametrizer._get_user_data(None)
        self.assertListEqual(expected, list(result.keys()))

    def test_collect(self):
        expected = ["message"]
        parametrizer = BasicParametrizer(self.user, {})
        result = parametrizer._get_user_data(None)
        self.assertListEqual(expected, list(result.keys()))
