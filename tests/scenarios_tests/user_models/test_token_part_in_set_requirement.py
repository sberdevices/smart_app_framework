# coding: utf-8
import unittest
from scenarios.scenario_models.field_requirements.field_requirements import TokenPartInSet


class RequirementTest(unittest.TestCase):

    def test_token_part_in_set_requirement_equal_false(self):
        requirement_items ={
              "type": "token_part_in_set",
              "part": "locality_type",
              "values": ["DISTRICT", "REGION"]
            }
        token_val = {'value': 'Амадора',
                     'locality_type': 'CITY',
                     'latitude': 38.75382,
                     'longitude': -9.23083,
                     'capital': None,
                     'locative_value': None,
                     'timezone': [[None, 1.0]],
                     'currency': ['EUR', 'евро'],
                     'country': 'Португалия',
                     'country_hidden': False}
        requirement = TokenPartInSet(requirement_items)
        self.assertFalse(requirement.check(token_val))

    def test_token_part_in_set_requirement_equal_true(self):
        requirement_items ={
              "type": "token_part_in_set",
              "part": "locality_type",
              "values": ["DISTRICT", "CITY"]
            }
        token_val = {'value': 'Амадора',
                     'locality_type': 'CITY',
                     'latitude': 38.75382,
                     'longitude': -9.23083,
                     'capital': None,
                     'locative_value': None,
                     'timezone': [[None, 1.0]],
                     'currency': ['EUR', 'евро'],
                     'country': 'Португалия',
                     'country_hidden': False}
        requirement = TokenPartInSet(requirement_items)
        self.assertTrue(requirement.check(token_val))

    def test_token_part_in_set_requirement_equal_False_double_empty(self):
        requirement_items ={
              "type": "token_part_in_set",
              "part": "locality_type",
              "values": []
            }
        token_val = {'value': 'Амадора',
                     'latitude': 38.75382,
                     'longitude': -9.23083,
                     'capital': None,
                     'locative_value': None,
                     'timezone': [[None, 1.0]],
                     'currency': ['EUR', 'евро'],
                     'country': 'Португалия',
                     'country_hidden': False,
                     'locality_type': []}
        requirement = TokenPartInSet(requirement_items)
        self.assertFalse(requirement.check(token_val))

    def test_token_part_in_set_requirement_equal_False_empty_val_none(self):
        requirement_items ={
              "type": "token_part_in_set",
              "part": "locality_type",
              "values": []
            }
        token_val = {'value': 'Амадора',
                     'latitude': 38.75382,
                     'longitude': -9.23083,
                     'capital': None,
                     'locative_value': None,
                     'timezone': [[None, 1.0]],
                     'currency': ['EUR', 'евро'],
                     'country': 'Португалия',
                     'country_hidden': False,
                     'locality_type': None}
        requirement = TokenPartInSet(requirement_items)
        self.assertFalse(requirement.check(token_val))

    def test_token_part_in_set_requirement_equal_False_string(self):
        requirement_items ={
              "type": "token_part_in_set",
              "part": "value",
              "values": 'cba'
            }
        token_val = {'value': 'abc',
                     'latitude': 38.75382,
                     'longitude': -9.23083,
                     'capital': None,
                     'locative_value': None,
                     'timezone': [[None, 1.0]],
                     'currency': ['EUR', 'евро'],
                     'country': 'Португалия',
                     'country_hidden': False}
        requirement = TokenPartInSet(requirement_items)
        self.assertFalse(requirement.check(token_val))

    def test_token_part_in_set_requirement_equal_False(self):
        requirement_items ={
              "type": "token_part_in_set",
              "part": "country_hidden",
              "values": [1, 2, 3]
            }
        token_val = {'value': 'Амадора',
                     'latitude': 38.75382,
                     'longitude': -9.23083,
                     'capital': None,
                     'locative_value': None,
                     'timezone': [[None, 1.0]],
                     'currency': ['EUR', 'евро'],
                     'country': 'Португалия',
                     'country_hidden': False}
        requirement = TokenPartInSet(requirement_items)
        self.assertFalse(requirement.check(token_val))

    def test_token_part_in_set_requirement_equal_False_val_int(self):
        requirement_items ={
              "type": "token_part_in_set",
              "part": 'capital',
              "values": [-9.23083]
            }
        token_val = {'value': 'Амадора',
                     'latitude': 38.75382,
                     'longitude': -9.23083,
                     'capital': None,
                     'locative_value': None,
                     'timezone': [[None, 1.0]],
                     'currency': ['EUR', 'евро'],
                     'country': 'Португалия',
                     'country_hidden': False}
        requirement = TokenPartInSet(requirement_items)
        self.assertFalse(requirement.check(token_val))

    def test_token_part_in_set_requirement_equal_True_arr(self):
        requirement_items ={
              "type": "token_part_in_set",
              "part": 'timezone',
              "values": [[[None, 1.0]]]
            }
        token_val = {'value': 'Амадора',
                     'latitude': 38.75382,
                     'longitude': -9.23083,
                     'capital': None,
                     'locative_value': None,
                     'timezone': [[None, 1.0]],
                     'currency': ['EUR', 'евро'],
                     'country': 'Португалия',
                     'country_hidden': False}
        requirement = TokenPartInSet(requirement_items)
        self.assertTrue(requirement.check(token_val))

    def test_token_part_in_set_requirement_equal_False_arr(self):
        requirement_items ={
              "type": "token_part_in_set",
              "part": 'timezone',
              "values": [[[1.0, None]]]
            }
        token_val = {'value': 'Амадора',
                     'latitude': 38.75382,
                     'longitude': -9.23083,
                     'capital': None,
                     'locative_value': None,
                     'timezone': [[None, 1.0]],
                     'currency': ['EUR', 'евро'],
                     'country': 'Португалия',
                     'country_hidden': False}
        requirement = TokenPartInSet(requirement_items)
        self.assertFalse(requirement.check(token_val))
