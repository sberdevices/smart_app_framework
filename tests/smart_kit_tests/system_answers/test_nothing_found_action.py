# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.system_answers import nothing_found_action
from core.basic_models.actions.string_actions import StringAction
from smart_kit.names.message_names import NOTHING_FOUND
from core.basic_models.actions.command import Command


class SystemAnswersTest1(unittest.TestCase):
    def setUp(self):
        self.test_command_1 = Mock('Command')
        self.test_id = '123-345-678'  # пусть чему-то равняется
        self.test_items1 = {"123-ASDF": {"command": [], "no_empty_nodes": True}}
        self.test_text_preprocessing_result = Mock('text_preprocessing_result')
        self.test_user1 = Mock('user')
        self.test_user1.parametrizer = Mock('parametrizer')
        self.test_user1.parametrizer.collect = lambda x, filter_params: {'input': x, 'result': x}

    def test_system_answers_nothing_found_action_init(self):
        obj1 = nothing_found_action.NothingFoundAction()
        obj2 = nothing_found_action.NothingFoundAction(self.test_items1, self.test_id)
        self.assertIsNone(obj1.id)
        self.assertTrue(obj2.id == self.test_id)
        self.assertTrue(isinstance(obj1._action, StringAction))
        self.assertTrue(obj1._action.command == NOTHING_FOUND)

    def test_system_answer_nothing_found_action_run(self):
        obj1 = nothing_found_action.NothingFoundAction()
        obj2 = nothing_found_action.NothingFoundAction(self.test_items1, self.test_id)
        self.assertTrue(isinstance(obj1.run(self.test_user1, self.test_text_preprocessing_result).pop(), Command))
        self.assertTrue(isinstance(obj2.run(self.test_user1, self.test_text_preprocessing_result).pop(), Command))
