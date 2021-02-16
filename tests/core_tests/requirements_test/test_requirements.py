# coding: utf-8
import unittest
from time import time
from unittest.mock import Mock

from core.model.registered import registered_factories
from core.basic_models.operators.operators import Operator

from core.basic_models.requirement.basic_requirements import Requirement, CompositeRequirement, AndRequirement, \
    OrRequirement, NotRequirement, RandomRequirement, TopicRequirement, TemplateRequirement, RollingRequirement, \
    TimeRequirement, DateTimeRequirement
from core.basic_models.requirement.device_requirements import ChannelRequirement
from core.basic_models.requirement.counter_requirements import CounterValueRequirement, CounterUpdateTimeRequirement


class MockRequirement:
    def __init__(self, items=None):
        items = items or {}
        self.cond = items.get("cond") or False

    def check(self, text_preprocessing_result, user, params):
        return self.cond


class MockTextNormalizationResult:
    def __init__(self, normalized=None, number_of_numbers=None, currencies_number=None, tokens=None):
        number_of_numbers = number_of_numbers or 0
        currencies_number = currencies_number or 0
        if normalized:
            self.words_tokenized = list(token.get("text") for token in normalized)
            self.words_tokenized_set = set(self.words_tokenized)
        else:
            self.words_tokenized = list()
            self.words_tokenized_set = set()
        self.number_of_numbers = number_of_numbers
        self.currencies_number = currencies_number
        self.tokenized_elements_list = tokens


class MockAmountOperator:
    def __init__(self, items):
        self.amount = items["amount"]

    def compare(self, value):
        return value > self.amount


class MockOperator:
    def __init__(self, amount):
        self.amount = amount

    def compare(self, value):
        return value > self.amount


class EQMockOperator:
    def __init__(self, amount):
        self.amount = amount

    def compare(self, value):
        return value == self.amount


class RequirementTest(unittest.TestCase):
    def test_base(self):
        requirement = Requirement(None)
        assert requirement.check(None, None)

    def test_composite(self):
        registered_factories[Requirement] = MockRequirement
        requirement = CompositeRequirement({"requirements": [
            {"cond": True},
            {"cond": True}
        ]})
        self.assertEqual(len(requirement.requirements), 2)
        self.assertTrue(requirement.check(None, None))

    def test_and_success(self):
        registered_factories[Requirement] = MockRequirement
        requirement = AndRequirement({"requirements": [
            {"cond": True},
            {"cond": True}
        ]})
        self.assertTrue(requirement.check(None, None))

    def test_and_fail(self):
        registered_factories[Requirement] = MockRequirement
        requirement = AndRequirement({"requirements": [
            {"cond": True},
            {"cond": False}
        ]})
        self.assertFalse(requirement.check(None, None))

    def test_or_success(self):
        registered_factories[Requirement] = MockRequirement
        requirement = OrRequirement({"requirements": [
            {"cond": True},
            {"cond": False}
        ]})
        self.assertTrue(requirement.check(None, None))

    def test_or_fail(self):
        registered_factories[Requirement] = MockRequirement
        requirement = OrRequirement({"requirements": [
            {"cond": False},
            {"cond": False}
        ]})
        self.assertFalse(requirement.check(None, None))

    def test_not_success(self):
        registered_factories[Requirement] = MockRequirement
        requirement = NotRequirement({"requirement": {"cond": False}})
        self.assertTrue(requirement.check(None, None))

    def test_not_fail(self):
        registered_factories[Requirement] = MockRequirement
        requirement = NotRequirement({"requirement": {"cond": True}})
        self.assertFalse(requirement.check(None, None))

    def test_channel_success(self):
        user = Mock()
        message = Mock(channel="ch1")
        user.message = message
        requirement = ChannelRequirement({"channels": ["ch1"]})
        text_normalization_result = None
        self.assertTrue(requirement.check(text_normalization_result, user))

    def test_channel_fail(self):
        user = Mock()
        message = Mock(channel="ch2")
        user.message = message
        requirement = ChannelRequirement({"channels": ["ch1"]})
        text_normalization_result = None
        self.assertFalse(requirement.check(text_normalization_result, user))

    def test_random_requirement_true(self):
        requirement = RandomRequirement({"percent": 100})
        self.assertTrue(requirement.check(None, None))

    def test_random_requirement_false(self):
        requirement = RandomRequirement({"percent": 0})
        self.assertFalse(requirement.check(None, None))

    def test_topic_requirement(self):
        requirement = TopicRequirement({"topics": ["test"]})
        user = Mock()
        message = Mock()
        message.topic_key = "test"
        user.message = message
        self.assertTrue(requirement.check(None, user))

    def test_counter_value_requirement(self):
        registered_factories[Operator] = MockAmountOperator
        user = Mock()
        counter = Mock()
        counter.__gt__ = Mock(return_value=True)
        user.counters = {"test": counter}
        requirement = CounterValueRequirement({"operator": {"type": "equal", "amount": 2}, "key": "test"})
        self.assertTrue(requirement.check(None, user))

    def test_counter_time_requirement(self):
        registered_factories[Operator] = MockAmountOperator
        user = Mock()
        counter = Mock()
        counter.update_time = int(time()) - 10
        user.counters = {"test": counter}
        requirement = CounterUpdateTimeRequirement({"operator": {"type": "more_or_equal", "amount": 5}, "key": "test"})
        self.assertTrue(requirement.check(None, user))

    def test_template_req_true(self):
        items = {
            "template": "{{ payload.message.strip() in payload.murexIds }}"
        }
        requirement = TemplateRequirement(items)
        params = {"payload": {
            "groupCode": "BROKER",
            "murexIds": ["AAA", "BBB"],
            "message": " BBB    "
        }}
        user = Mock()
        user.parametrizer = Mock()
        user.parametrizer.collect = Mock(return_value=params)
        self.assertTrue(requirement.check(None, user))

    def test_template_req_false(self):
        items = {
            "template": "{{ payload.groupCode == 'BROKER' }}"
        }
        requirement = TemplateRequirement(items)
        params = {"payload": {"groupCode": "BROKER1"}}
        user = Mock()
        user.parametrizer = Mock()
        user.parametrizer.collect = Mock(return_value=params)
        self.assertFalse(requirement.check(None, user))

    def test_template_req_raise(self):
        items = {
            "template": "{{ payload.groupCode }}"
        }
        requirement = TemplateRequirement(items)
        params = {"payload": {"groupCode": "BROKER1"}}
        user = Mock()
        user.parametrizer = Mock()
        user.parametrizer.collect = Mock(return_value=params)
        self.assertRaises(TypeError, requirement.check, None, user)

    def test_rolling_requirement_true(self):
        user = Mock()
        user.id = "353454"
        requirement = RollingRequirement({"percent": 100})
        text_normalization_result = None
        self.assertTrue(requirement.check(text_normalization_result, user))

    def test_rolling_requirement_false(self):
        user = Mock()
        user.id = "353454"
        requirement = RollingRequirement({"percent": 0})
        text_normalization_result = None
        self.assertFalse(requirement.check(text_normalization_result, user))

    def test_time_requirement_true(self):
        user = Mock()
        user.id = "353454"
        user.message.payload = {
            "meta": {
                "time": {
                    "timestamp": 1610990255000,  # ~ 2021-01-18 17:17:35
                    "timezone_offset_sec": 1000000000,  # shouldn't affect
                }
            }
        }
        requirement = TimeRequirement(
            {
                "operator": {
                    "type": "more",
                    "amount": "17:00:00",
                }
            }
        )
        text_normalization_result = None
        self.assertTrue(requirement.check(text_normalization_result, user))

    def test_time_requirement_false(self):
        user = Mock()
        user.id = "353454"
        user.message.payload = {
            "meta": {
                "time": {
                    "timestamp": 1610979455663,  # ~ 2021-01-18 17:17:35
                    "timezone_offset_sec": 1000000000,  # shouldn't affect
                }
            }
        }
        requirement = TimeRequirement(
            {
                "operator": {
                    "type": "more",
                    "amount": "18:00:00",
                }
            }
        )
        text_normalization_result = None
        self.assertFalse(requirement.check(text_normalization_result, user))

    def test_datetime_requirement_true(self):
        user = Mock()
        user.id = "353454"
        user.message.payload = {
            "meta": {
                "time": {
                    "timestamp": 1610979455663,  # ~ 2021-01-18 17:17:35
                    "timezone_offset_sec": 1000000000,  # shouldn't affect
                }
            }
        }
        requirement = DateTimeRequirement(
            {
                "match_cron": "*/17 14-19 * * mon"
            }
        )
        text_normalization_result = None
        self.assertTrue(requirement.check(text_normalization_result, user))

    def test_datetime_requirement_false(self):
        user = Mock()
        user.id = "353454"
        user.message.payload = {
            "meta": {
                "time": {
                    "timestamp": 1610979455663,  # ~ 2021-01-18 17:17:35
                    "timezone_offset_sec": 1000000000,  # shouldn't affect
                }
            }
        }
        requirement = DateTimeRequirement(
            {
                "match_cron": "* * * * 6,7"
            }
        )
        text_normalization_result = None
        self.assertFalse(requirement.check(text_normalization_result, user))


if __name__ == '__main__':
    unittest.main()
