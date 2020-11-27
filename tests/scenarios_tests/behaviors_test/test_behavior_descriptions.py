# coding: utf-8
import unittest
from unittest.mock import Mock
from scenarios.behaviors import behavior_descriptions


class BehaviorsTest2(unittest.TestCase):
    def setUp(self):
        self.test_items = {"success_action": []}

    def test_behavior_descriptions_init(self):
        obj = behavior_descriptions.BehaviorDescriptions(self.test_items)
        # self.assertTrue(hasattr(obj, 'misstate'))
        self.assertTrue(hasattr(obj, 'update_data'))
