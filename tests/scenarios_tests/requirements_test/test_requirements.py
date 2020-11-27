# coding: utf-8
import unittest
from unittest.mock import Mock

from scenarios.requirements.requirements import TemplateInArrayRequirement, ArrayItemInTemplateRequirement, RegexpInTemplateRequirement


class MockRequirement:
    def __init__(self, items=None):
        items = items or {}
        self.cond = items.get("cond") or False

    def check(self, text_preprocessing_result, user):
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

    def test_template_in_array_req_true(self):
        items = {
            "template": "{{ payload.userInfo.tbcode }}",
            "items": ["32", "33"]
        }
        requirement = TemplateInArrayRequirement(items)
        params = {"payload": {
            "userInfo": {
                "tbcode": "32"
            },
            "message": "BBB"
        }}
        user = Mock()
        user.parametrizer = Mock()
        user.parametrizer.collect = Mock(return_value=params)
        self.assertTrue(requirement.check(None, user))

    def test_template_in_array_req_true2(self):
            items = {
                "template": "{{ payload.message.strip() }}",
                "items": ["AAA", "BBB", "CCC"]
            }
            requirement = TemplateInArrayRequirement(items)
            params = {"payload": {
                "userInfo": {
                    "tbcode": "32"
                },
                "message": " BBB    "
            }}
            user = Mock()
            user.parametrizer = Mock()
            user.parametrizer.collect = Mock(return_value=params)
            self.assertTrue(requirement.check(None, user))

    def test_template_in_array_req_false(self):
            items = {
                "template": "{{ payload.message.strip() }}",
                "items": ["AAA", "CCC"]
            }
            requirement = TemplateInArrayRequirement(items)
            params = {"payload": {
                "userInfo": {
                    "tbcode": "32",
                },
                "message": " BBB "
            }}
            user = Mock()
            user.parametrizer = Mock()
            user.parametrizer.collect = Mock(return_value=params)
            self.assertFalse(requirement.check(None, user))


    def test_array_in_template_req_true(self):
            items = {
                "template": {
                    "type": "unified_template",
                    "template": "{{ payload.userInfo.departcode.split('/')|tojson }}",
                    "loader": "json"
                },
                "items": ["111", "456"]
            }
            requirement = ArrayItemInTemplateRequirement(items)
            params = {"payload": {
                "userInfo": {
                    "tbcode": "32",
                    "departcode": "123/2345/456"
                },
                "message": " BBB "
            }}
            user = Mock()
            user.parametrizer = Mock()
            user.parametrizer.collect = Mock(return_value=params)
            self.assertTrue(requirement.check(None, user))


    def test_array_in_template_req_true2(self):
            items = {
                "template": "{{ payload.message.strip() }}",
                "items": ["AAA", "BBB"]
            }
            requirement = ArrayItemInTemplateRequirement(items)
            params = {"payload": {
                "userInfo": {
                    "tbcode": "32",
                    "departcode": "123/2345/456"
                },
                "message": " BBB "
            }}
            user = Mock()
            user.parametrizer = Mock()
            user.parametrizer.collect = Mock(return_value=params)
            self.assertTrue(requirement.check(None, user))


    def test_array_in_template_req_false(self):
            items = {
                "template": {
                    "type": "unified_template",
                    "template": "{{ payload.userInfo.departcode.split('/')|tojson }}",
                    "loader": "json"
                },
                "items": ["111", "222"]
            }
            requirement = ArrayItemInTemplateRequirement(items)
            params = {"payload": {
                "userInfo": {
                    "tbcode": "32",
                    "departcode": "123/2345/456"
                },
                "message": " BBB "
            }}
            user = Mock()
            user.parametrizer = Mock()
            user.parametrizer.collect = Mock(return_value=params)
            self.assertFalse(requirement.check(None, user))


    def test_regexp_in_template_req_true(self):
            items = {
                "template": "{{ payload.message.strip() }}",
                "regexp": "(^|\s)[Фф](\.|-)?1(\-)?(у|У)?($|\s)"
            }
            requirement = RegexpInTemplateRequirement(items)
            params = {"payload": {
                "userInfo": {
                    "tbcode": "32",
                },
                "message": "карточки ф1у"
            }}
            user = Mock()
            user.parametrizer = Mock()
            user.parametrizer.collect = Mock(return_value=params)
            self.assertTrue(requirement.check(None, user))


    def test_regexp_in_template_req_false(self):
            items = {
                "template": "{{ payload.message.strip() }}",
                "regexp": "(^|\s)[Фф](\.|-)?1(\-)?(у|У)?($|\s)"
            }
            requirement = RegexpInTemplateRequirement(items)
            params = {"payload": {
                "userInfo": {
                    "tbcode": "32",
                },
                "message": "карточки конг фу 1"
            }}
            user = Mock()
            user.parametrizer = Mock()
            user.parametrizer.collect = Mock(return_value=params)
            self.assertFalse(requirement.check(None, user))




if __name__ == '__main__':
    unittest.main()
