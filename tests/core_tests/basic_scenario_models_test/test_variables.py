# coding: utf-8
import unittest

from core.basic_models.variables.variables import Variables


class VariablesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.variables = Variables(None, None)

    def test_set(self):
        self.variables.set("key", "value")
        self.assertEqual(self.variables.values, {"key": "value"})

    def test_get(self):
        self.variables.set("key", "value")
        self.assertEqual(self.variables.get("key"), "value")
        self.assertEqual(self.variables.get("nonexistkey", "defaultvalue"), "defaultvalue")

    def test_update(self):
        self.variables.set("key", "value")
        self.variables.update("key", "newvalue")
        self.assertEqual(self.variables.get("key"), "newvalue")

    def test_delete(self):
        self.variables.set("key", "value")
        self.variables.delete("key")
        self.assertEqual(self.variables.values, {})

    def test_expire(self):
        self.variables.set("key", "value", ttl=0)
        self.assertEqual(self.variables.values, {})

    def test_clear(self):
        self.variables.set("key_1", "value_1")
        self.variables.set("key_2", "value_2")
        self.variables.clear()
        self.assertEqual(self.variables.values, {})
