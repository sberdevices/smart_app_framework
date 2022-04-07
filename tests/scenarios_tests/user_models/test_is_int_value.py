# coding: utf-8
from unittest import IsolatedAsyncioTestCase

from scenarios.scenario_models.field_requirements.field_requirements import IsIntFieldRequirement


class IsIntFieldRequirementTest(IsolatedAsyncioTestCase):

    def setUp(self):
        items = {}
        self.requirement = IsIntFieldRequirement(items)

    async def test_is_int_number_string(self):
        text = "123"
        self.assertTrue(await self.requirement.check(text))

    async def test_is_int_float_string(self):
        text = "1.23"
        self.assertFalse(await self.requirement.check(text))

    async def test_is_int_text_string(self):
        text = "test"
        self.assertFalse(await self.requirement.check(text))

    async def test_is_int_empty_string(self):
        text = ""
        self.assertFalse(await self.requirement.check(text))
