# -*- coding: utf-8 -*-
import sys
import unittest

from core.model.field import Field
from core.model.model import Model


class MockField():
    def __init__(self, value, description, *args):
        self.value = value
        self.descr = description

    @property
    def raw(self):
        return self.value

    def fill(self, origin_value):
        self.value = origin_value
        return True


class MockModel(Model):
    @property
    def fields(self):
        return [Field("field1", MockField, "field1_descr")]


class ModelTest(unittest.TestCase):
    def setUp(self):
        self.model = MockModel(values={"field1": "field1_data"}, user=None)

    def test_get_field(self):
        field1 = self.model.get_field("field1")
        assert field1.value, field1.descr == ("field1_data", "field1_descr")

    def test_get_field_error(self):
        exception = None
        try:
            self.model.get_field("field_unknown")
        except AttributeError:
            exception = sys.exc_info()[0]
        assert exception == AttributeError

    def test_raw(self):
        raw = self.model.raw
        assert raw == dict(field1="field1_data")


if __name__ == '__main__':
    unittest.main()
