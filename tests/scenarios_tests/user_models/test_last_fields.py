import time
from unittest import TestCase

from scenarios.user.last_fields.last_fields import LastFields


class LastFieldsTest(TestCase):
    def test_expire_some(self):
        current_time = time.time()
        field_1 = {
            "value": 1,
            "remove_time": current_time + 100
        }
        field_2 = {
            "value": 2,
            "remove_time": current_time - 1
        }
        name_1 = "test_filed_1"
        fields = LastFields({name_1: field_1, "test_field_2": field_2}, None)
        fields.expire()
        self.assertDictEqual(fields.raw, {name_1: field_1})

    def test_expire_all(self):
        remove_time = time.time() - 100
        field_1 = {
            "value": 1,
            "remove_time": remove_time
        }

        field_2 = {
            "value": 2,
            "remove_time": remove_time - 100
        }
        fields = LastFields({"test_field_1": field_1, "test_field_2": field_2}, None)
        fields.expire()
        self.assertDictEqual(fields.raw, {})

    def test_expire_none(self):
        current_time = time.time() + 100
        field_1 = {
            "value": 1,
            "remove_time": current_time
        }
        field_2 = {
            "value": 2,
            "remove_time": current_time + 100
        }
        name_1 = "test_field_1"
        name_2 = "test_field_2"
        fields = LastFields({name_1: field_1, name_2: field_2}, None)
        fields.expire()
        self.assertDictEqual(fields.raw, {name_1: field_1, name_2: field_2})

    def test_expire_not_set(self):
        field_1 = {"value": 1}
        field_2 = {"value": 2}
        name_1 = "test_field_1"
        name_2 = "test_field_2"
        fields = LastFields({name_1: field_1, name_2: field_2}, None)
        fields.expire()
        self.assertDictEqual(fields.raw, {name_1: field_1, name_2: field_2})
