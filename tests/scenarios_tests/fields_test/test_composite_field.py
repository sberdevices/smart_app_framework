# coding: utf-8
from unittest import TestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.composite_field import CompositeField
from scenarios.scenario_models.field.field import field_models


class MockDescr1():
    def __init__(self, *args, **kwargs):
        self.id = "d1"


class MockDescr2():
    def __init__(self, *args, **kwargs):
        self.id = "d2"


class MockItem1():
    def __init__(self, *args, **kwargs):
        self.available = False
        self.value = "raw"
        pass

    def set_available(self):
        pass

    def fill(self, value):
        self.value = value

    @property
    def valid(self):
        return True

    @property
    def raw(self):
        return self.value


class MockItem2(MockItem1):
    pass


field_models[MockDescr1] = MockItem1
field_models[MockDescr2] = MockItem2


class TestCompositeField(TestCase):
    def setUp(self):
        descr1 = MockDescr1(id="descr1")
        descr2 = MockDescr2(id="descr2")
        descriptions = {"d1": descr1, "d2": descr2}
        user = Mock()
        fields = {"fields": {"d1": {}, "d2": {}}}
        self.composite_field = CompositeField(Mock(fields=descriptions), fields, user, None)

    def test_available1(self):
        self.assertFalse(self.composite_field.available)

    def test_available2(self):
        self.composite_field.fields["d1"].available = True
        self.composite_field.fields["d2"].available = True
        self.assertTrue(self.composite_field.available)

    def test_set_available(self):
        self.composite_field.set_available()
        for field_descr in self.composite_field.fields:
            self.composite_field.fields[field_descr].available = True

    def test_raw(self):
        expected = {'fields': {'d1': 'raw', 'd2': 'raw'}}
        raw = self.composite_field.raw
        self.assertEqual(expected, raw)

    def test_fill(self):
        expected = {'fields': {'d1': 'v1', 'd2': 'v2'}}
        value = {"d1": "v1", "d2": "v2"}
        self.composite_field.fill(value)
        raw = self.composite_field.raw
        self.assertEqual(expected, raw)

    def test_value(self):
        expected = {'d1': 'raw', 'd2': 'raw'}
        result = self.composite_field.value
        self.assertEqual(expected, result)

    def test_valid(self):
        result = self.composite_field.valid
        self.assertTrue(result)
