# coding: utf-8
import unittest
from smart_kit.text_preprocessing import http_text_normalizer


class TextPrerocessingTest2(unittest.TestCase):
    def setUp(self):
        self.test_text = 'Any text'
        self.test_context = ['Any context']
        self.test_message_type = 'Any message'

    def test_normalization_words_tokenized_set(self):
        self.assertTrue(http_text_normalizer.words_tokenized_set('a s d f') == {'a', 's', 'd', 'f'})
        self.assertTrue(http_text_normalizer.words_tokenized_set(' ') == {'', '', ''})

    def test_normalization_print_current_state_init(self):
        obj1 = http_text_normalizer.HttpTextNormalizer("http://any-url", 111, 8, True)
        self.assertTrue(obj1.TEXT_PARAM_NAME == "text")
        self.assertTrue(obj1.NORMALIZE_METHOD == "normalize")
        self.assertTrue(obj1._preprocess_url == 'http://any-url/preprocess')
        self.assertTrue(obj1._classify_url == 'http://any-url/classify')
        self.assertTrue(obj1._normalize_url == 'http://any-url/normalize')
        self.assertTrue(obj1._timeout == 8)
        self.assertTrue(obj1._verbose)
        self.assertTrue(obj1._tqdm_func == http_text_normalizer.tqdm)

    def test_normalization_set_preprocess_mode(self):
        obj1 = http_text_normalizer.HttpTextNormalizer("http://any-url", 111, 8, True)
        obj2 = http_text_normalizer.HttpTextNormalizer("http://any-url", 111, 8, False)
        obj1.set_preprocess_mode()
        obj1.set_classify_mode()
        obj1.set_normalize_mode()
        obj2.set_preprocess_mode()
        obj2.set_classify_mode()
        obj2.set_normalize_mode()
