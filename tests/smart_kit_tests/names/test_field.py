# coding: utf-8
import unittest
from core.names import field


class FieldTest1(unittest.TestCase):
    def test_fields(self):
        self.assertIsNotNone(field.PRONOUNCE_TEXT)
        self.assertIsNotNone(field.ITEMS)
        self.assertIsNotNone(field.MESSAGE_NAME)
        self.assertIsNotNone(field.AUTO_LISTENING)
        self.assertIsNotNone(field.FINISHED)
        self.assertIsNotNone(field.DEVICE)
        self.assertIsNotNone(field.SUB)
        self.assertIsNotNone(field.USER_ID)
        self.assertIsNotNone(field.USER_CHANNEL)
        self.assertIsNotNone(field.SMART_BIO)
        self.assertIsNotNone(field.SERVER_ACTION)
        self.assertIsNotNone(field.PROJECT_NAME)
        self.assertIsNotNone(field.INTENT)
        self.assertIsNotNone(field.INTENT_META)
        self.assertIsNotNone(field.APP_INFO)
        self.assertIsNotNone(field.PROJECT_ID)
        self.assertIsNotNone(field.APPLICATION_ID)
        self.assertIsNotNone(field.APP_VERSION_ID)
        self.assertIsNotNone(field.FRONTEND_ENDPOINT)
        self.assertIsNotNone(field.FRONTEND_TYPE)
