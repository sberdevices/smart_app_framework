# coding: utf-8
import asyncio
from unittest import TestCase

from scenarios.scenario_models.field_requirements.field_requirements import IsIntFieldRequirement


class IsIntFieldRequirementTest(TestCase):

    @classmethod
    def setUpClass(cls):
        items = {}
        cls.requirement = IsIntFieldRequirement(items)

    def test_is_int_number_string(self):
        text = "123"
        loop = asyncio.get_event_loop()
        self.assertTrue(loop.run_until_complete(self.requirement.check(text)))

    def test_is_int_float_string(self):
        text = "1.23"
        loop = asyncio.get_event_loop()
        self.assertFalse(loop.run_until_complete(self.requirement.check(text)))

    def test_is_int_text_string(self):
        text = "test"
        loop = asyncio.get_event_loop()
        self.assertFalse(loop.run_until_complete(self.requirement.check(text)))

    def test_is_int_empty_string(self):
        text = ""
        loop = asyncio.get_event_loop()
        self.assertFalse(loop.run_until_complete(self.requirement.check(text)))
