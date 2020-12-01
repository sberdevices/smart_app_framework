# coding: utf-8
import unittest
from smart_kit.names import message_names


class MessageNamesTest1(unittest.TestCase):
    def test_message_names(self):
        self.assertIsNotNone(message_names.ANSWER_TO_USER)
        self.assertIsNotNone(message_names.ERROR)
        self.assertIsNotNone(message_names.NOTHING_FOUND)
        self.assertIsNotNone(message_names.MESSAGE_TO_SKILL)
        self.assertIsNotNone(message_names.LOCAL_TIMEOUT)
        self.assertIsNotNone(message_names.RUN_APP)
        self.assertIsNotNone(message_names.CLOSE_APP)
        self.assertIsNotNone(message_names.SERVER_ACTION)
