import os
from unittest import TestCase
from unittest.mock import Mock, patch

from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
import smart_kit
from scenarios.scenario_models.field.field_filler_description import (
    ApproveFiller,
    ApproveRawTextFiller
)
from smart_kit.text_preprocessing.local_text_normalizer import LocalTextNormalizer


def patch_get_app_config(mock_get_app_config):
    result = Mock()
    sk_path = os.path.dirname(smart_kit.__file__)
    result.STATIC_PATH = os.path.join(sk_path, 'template/static')
    mock_get_app_config.return_value = result
    result.NORMALIZER = LocalTextNormalizer()
    mock_get_app_config.return_value = result


class TestApproveFiller(TestCase):

    @patch('smart_kit.configs.get_app_config')
    def test_1(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config)
        items = {
            'yes_words': [
                'да',
                'конечно',
                'давай',
                'ага',
                'хорошо',
                'именно',
                'можно'
            ],
            'no_words': [
                'нет',
                'не',
                'ни',
                'нельзя',
                'отнюдь',
                'нету'
            ]
        }
        filler = ApproveFiller(items)
        normalizer = LocalTextNormalizer()

        user_phrase = 'даю'
        text_pre_result = TextPreprocessingResult(normalizer(user_phrase))
        result = filler.extract(text_pre_result, None)
        self.assertTrue(result)

        user_phrase = 'да нет'
        text_pre_result = TextPreprocessingResult(normalizer(user_phrase))
        result = filler.extract(text_pre_result, None)
        self.assertFalse(result)

        user_phrase = 'даю добро'
        text_pre_result = TextPreprocessingResult(normalizer(user_phrase))
        result = filler.extract(text_pre_result, None)
        self.assertIsNone(result)


class TestApproveRawTextFiller(TestCase):

    @patch('smart_kit.configs.get_app_config')
    def test_1(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config)
        items = {
            'yes_words': [
                'да',
                'конечно',
                'давай',
                'ага',
                'хорошо',
                'именно',
                'можно'
            ],
            'no_words': [
                'нет',
                'не',
                'ни',
                'нельзя',
                'отнюдь',
                'нету'
            ]
        }
        filler = ApproveRawTextFiller(items)
        normalizer = LocalTextNormalizer()

        user_phrase = 'конечно'
        text_pre_result = TextPreprocessingResult(normalizer(user_phrase))
        result = filler.extract(text_pre_result, None)
        self.assertTrue(result)

        user_phrase = 'да нет'
        text_pre_result = TextPreprocessingResult(normalizer(user_phrase))
        result = filler.extract(text_pre_result, None)
        self.assertFalse(result)

        user_phrase = 'даю'
        text_pre_result = TextPreprocessingResult(normalizer(user_phrase))
        result = filler.extract(text_pre_result, None)
        self.assertIsNone(result)
