# coding: utf-8
from unittest import TestCase

from scenarios.scenario_models.field_requirements.field_requirements import IsIntFieldRequirement


class IsIntFieldRequirementTest(TestCase):

    @classmethod
    def setUpClass(cls):
        items = {}
        cls.requirement = IsIntFieldRequirement(items)

    def test_is_int_number_string(self):
        text = "123"
        self.assertTrue(self.requirement.check(text))

    def test_is_int_float_string(self):
        text = "1.23"
        self.assertFalse(self.requirement.check(text))

    def test_is_int_text_string(self):
        text = "test"
        self.assertFalse(self.requirement.check(text))

    def test_is_int_empty_string(self):
        text = ""
        self.assertFalse(self.requirement.check(text))
