# coding: utf-8
import unittest
from core.configs import global_constants


class GlobalConstantsTest1(unittest.TestCase):
    def test_constants(self):
        self.assertIsNotNone(global_constants.CALLBACK_ID_HEADER)
