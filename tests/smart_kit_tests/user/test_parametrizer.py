# coding: utf-8
import unittest
from unittest.mock import Mock
from scenarios.user import parametrizer


class TestMessage:
    payload = "any payload"
    uuid = "1234-5678-9102"


class UserTest1(unittest.TestCase):
    def setUp(self):
        self.test_user1 = Mock('User')
        self.test_user1.message = Mock('Message')
        self.test_user1.descriptions = {"scenarios": {11: 'any data 1', 12: 'any data 2'}}
        self.test_user1.last_scenarios = Mock('last scenario')
        self.test_user1.last_scenarios.last_scenario_name = 11
        self.test_items = {"123-ASDF": {"command": [], "no_empty_nodes": True}}
        self.test_scenario1 = Mock('scenario')
        self.test_scenario1.scenario_description = "This is test scenario 1 desc"
        self.test_scenario1.form_type = "any type 1"
        self.test_user2 = Mock('User')
        self.test_user2.message = Mock('Message')
        self.test_user2.descriptions = {"scenarios": {22: self.test_scenario1}}
        self.test_user2.last_scenarios = Mock('last scenario')
        self.test_user2.last_scenarios.last_scenario_name = 22
        self.test_user3 = Mock('User')
        self.test_user3.message = Mock('Message')
        self.test_user3.descriptions = {"scenarios": {22: self.test_scenario1}}
        self.test_user3.last_scenarios = Mock('last scenario')
        self.test_user3.last_scenarios.last_scenario_name = 33
        self.test_forms = {'any type 1': 'any form 1', 'any type 2': 'any form 2'}
        self.test_user4 = Mock('User')
        self.test_user4.forms = Mock('Forms')
        self.test_user4.forms.collect_form_fields = lambda: self.test_forms
        self.test_user4.message = TestMessage()
        self.test_user4.message.payload = "any payload"
        self.test_user4.message.uuid = "1234-5678-9102"
        self.test_user4.variables = Mock('Variables')
        self.test_user4.variables.values = [1, 2, 3]
        self.test_user4.counters = Mock('Counters')
        self.test_user4.counters.raw = 3
        self.test_user4.descriptions = {"scenarios": {22: self.test_scenario1}}
        self.test_user4.last_scenarios = Mock('last scenario')
        self.test_user4.last_scenarios.last_scenario_name = 22
        self.test_user4.gender_selector = Mock()
        self.test_user4.gender_selector.get_text_by_key = ''
        local_vars = Mock()
        local_vars.values = dict()
        self.test_user4.local_vars = local_vars
        self.test_text_preprocessing_result = Mock('text_preprocessing_result')
        self.test_text_preprocessing_result.raw = {1: "any text"}

    def test_parametrizer_SmartAppParametrize_init(self):
        obj = parametrizer.Parametrizer(self.test_user1, self.test_items)
        self.assertTrue(obj._user == self.test_user1)

    def test_parametrizer_SmartAppParametrize_get_scenario(self):
        obj = parametrizer.Parametrizer(self.test_user1, self.test_items)
        self.assertTrue(obj._get_scenario() == 'any data 1')

    def test_parametrizer_get_main_form(self):
        obj1 = parametrizer.Parametrizer(self.test_user2, self.test_items)
        obj2 = parametrizer.Parametrizer(self.test_user3, self.test_items)
        self.assertTrue(obj1._get_main_form(self.test_forms) == 'any form 1')
        self.assertIsNone(obj2._get_main_form(self.test_forms))

    def test_parametrizer_get_user_data(self):
        obj1 = parametrizer.Parametrizer(self.test_user4, self.test_items)
        answer1 = {'payload': 'any payload', 'uuid': '1234-5678-9102', 'forms': {
            'any type 1': 'any form 1', 'any type 2': 'any form 2'}, 'main_form': 'any form 1',
                   'text_preprocessing_result': {}, 'variables': [1, 2, 3], 'counters': 3, 'scenario_id': 22,
                   'gender_sensitive_text': '', 'local_vars': {}}
        answer2 = {'payload': 'any payload', 'uuid': '1234-5678-9102', 'forms': {
            'any type 1': 'any form 1', 'any type 2': 'any form 2'}, 'main_form': 'any form 1',
                   'text_preprocessing_result': {1: 'any text'}, 'variables': [1, 2, 3], 'counters': 3,
                   'scenario_id': 22, 'gender_sensitive_text': '', 'local_vars': {}}
        result1 = obj1._get_user_data()
        result1.pop('message')
        result2 = obj1._get_user_data(self.test_text_preprocessing_result)
        result2.pop('message')
        self.assertTrue(result1 == answer1)
        self.assertTrue(result2 == answer2)
