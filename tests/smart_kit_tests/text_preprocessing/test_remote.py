# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.text_preprocessing import remote


class TestTextAlt:
    def __init__(self, text):
        self.text = text

    def get_result(self, *argv, **kwargs):
        return self.text.lowercase()

    @classmethod
    def run(cls, x):
        return cls(x)


class TextPrerocessingTest1(unittest.TestCase):
    def setUp(self):
        self.test_text = 'Any text'
        self.test_context = ['Any context']
        self.test_message_type = 'Any message'

    def test_text_preprocessing_base_text_normalizer_init(self):
        obj1 = remote.BaseTextNormalizer(self.test_text)
        obj2 = remote.BaseTextNormalizer(self.test_text, '')
        obj3 = remote.BaseTextNormalizer(self.test_text, self.test_context, self.test_message_type)
        self.assertTrue(obj1.text == self.test_text)
        self.assertTrue(obj1.context == [])
        self.assertTrue(obj1.message_type == "text")
        self.assertTrue(obj2.text == self.test_text)
        self.assertTrue(obj2.context == [])
        self.assertTrue(obj2.message_type == "text")
        self.assertTrue(obj3.text == self.test_text)
        self.assertTrue(obj3.context == self.test_context)
        self.assertTrue(obj3.message_type == self.test_message_type)

    def test_text_preprocessing_base_text_normalizer_get_result(self):
        obj1 = remote.BaseTextNormalizer(self.test_text, self.test_context, self.test_message_type)
        with self.assertRaises(NotImplementedError):
            obj1.get_result(*(1, 2, 3), **{'first': 1, 'second': 2})
        with self.assertRaises(NotImplementedError):
            obj1.get_result()
        with self.assertRaises(NotImplementedError):
            obj1.get_result(*(1, 2, 3))
        with self.assertRaises(NotImplementedError):
            obj1.get_result(**{'first': 1, 'second': 2})

    def test_text_preprocessing_base_text_normalizer_normalize(self):
        obj1 = remote.BaseTextNormalizer(self.test_text, self.test_context, self.test_message_type)
        with self.assertRaises(NotImplementedError):
            self.assertTrue(obj1.normalize(self.test_text) == 'any text')
        with self.assertRaises(NotImplementedError):
            self.assertTrue(obj1.normalize(self.test_text,  *(1, 2)) == 'any text')
        with self.assertRaises(NotImplementedError):
            self.assertTrue(obj1.normalize(self.test_text, **{'first': 1, 'second': 2}) == 'any text')
        with self.assertRaises(NotImplementedError):
            self.assertTrue(obj1.normalize(self.test_text, *(1, 2), **{'first': 1, 'second': 2}) == 'any text')

