import os
from unittest import TestCase
from unittest.mock import Mock, patch

import smart_kit
from scenarios.scenario_models.field.field_filler_description import (
    IntersectionFieldFiller,
    IntersectionOriginalTextFiller
)
from smart_kit.text_preprocessing.local_text_normalizer import LocalTextNormalizer


def patch_get_app_config(mock_get_app_config):
    result = Mock()
    sk_path = os.path.dirname(smart_kit.__file__)
    result.STATIC_PATH = os.path.join(sk_path, 'template/static')
    mock_get_app_config.return_value = result
    result.NORMALIZER = LocalTextNormalizer()
    mock_get_app_config.return_value = result


class TestIntersectionFieldFiller(TestCase):

    @patch('smart_kit.configs.get_app_config')
    def test_1(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config)
        expected = 'лосось'
        items = {
            'cases': {
                'лосось': [
                    'хорошая рыба'
                ],
                'килька': [
                    'консервы'
                ]
            }
        }
        text_preprocessing_result = Mock()
        text_preprocessing_result.tokenized_elements_list = [
            {'lemma': 'весь'},
            {'lemma': 'хороший'},
            {'lemma': 'и'},
            {'lemma': 'спасибо'},
            {'lemma': 'за'},
            {'lemma': 'рыба'},
        ]

        filler = IntersectionFieldFiller(items)
        result = filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    @patch('smart_kit.configs.get_app_config')
    def test_2(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config)
        items = {}
        text_preprocessing_result = Mock()
        text_preprocessing_result.tokenized_elements_list = []

        filler = IntersectionFieldFiller(items)
        result = filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)

    @patch('smart_kit.configs.get_app_config')
    def test_3(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config)
        expected = 'дефолтный тунец'
        items = {
            'cases': {
                'лосось': [
                    'хорошая рыба'
                ],
                'килька': [
                    'консервы'
                ]
            },
            'default': 'дефолтный тунец'
        }
        text_preprocessing_result = Mock()
        text_preprocessing_result.tokenized_elements_list = [
            {'lemma': 'мой'},
            {'lemma': 'дядя'},
            {'lemma': 'самый'},
            {'lemma': 'честный'},
            {'lemma': 'правило'},
        ]

        filler = IntersectionFieldFiller(items)
        result = filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)


class TestIntersectionOriginalTextFiller(TestCase):
    @patch('smart_kit.configs.get_app_config')
    def test_1(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config)
        items = {
            'cases': {
                'лосось': [
                    'хорошая рыба'
                ],
                'килька': [
                    'консервы'
                ]
            }
        }
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = 'всего хорошего и спасибо за рыбу'

        filler = IntersectionOriginalTextFiller(items)
        result = filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)

    @patch('smart_kit.configs.get_app_config')
    def test_2(self, mock_get_app_config):
        expected = 'лосось'
        patch_get_app_config(mock_get_app_config)
        items = {
            'cases': {
                'лосось': [
                    'хорошая рыба'
                ],
                'килька': [
                    'консервы'
                ]
            }
        }
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = 'всего хорошая и спасибо за рыба'

        filler = IntersectionOriginalTextFiller(items)
        result = filler.extract(text_preprocessing_result, None)

        self.assertEqual(expected, result)

    @patch('smart_kit.configs.get_app_config')
    def test_3(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config)
        items = {
            'cases': {
                'лосось': [
                    'хорошая рыба'
                ],
                'килька': [
                    'консервы'
                ]
            },
            'exceptions': {
                'лосось': 'не хорошая рыба'
            },
        }
        text_preprocessing_result = Mock()
        text_preprocessing_result.original_text = 'не это хорошая рыба'

        filler = IntersectionOriginalTextFiller(items)
        result = filler.extract(text_preprocessing_result, None)

        self.assertIsNone(result)
