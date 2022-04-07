import asyncio
import os
import unittest
from time import time
from unittest.mock import Mock, patch

import smart_kit
from core.basic_models.classifiers.basic_classifiers import ExternalClassifier
from core.basic_models.operators.operators import Operator
from core.basic_models.requirement.basic_requirements import Requirement, CompositeRequirement, AndRequirement, \
    OrRequirement, NotRequirement, RandomRequirement, TopicRequirement, TemplateRequirement, RollingRequirement, \
    TimeRequirement, DateTimeRequirement, IntersectionRequirement, ClassifierRequirement, FormFieldValueRequirement, \
    EnvironmentRequirement, CharacterIdRequirement, FeatureToggleRequirement
from core.basic_models.requirement.counter_requirements import CounterValueRequirement, CounterUpdateTimeRequirement
from core.basic_models.requirement.device_requirements import ChannelRequirement
from core.basic_models.requirement.user_text_requirements import AnySubstringInLoweredTextRequirement, \
    PhoneNumberNumberRequirement, NumInRangeRequirement, IntersectionWithTokensSetRequirement, \
    NormalizedTextInSetRequirement
from core.model.registered import registered_factories
from smart_kit.text_preprocessing.local_text_normalizer import LocalTextNormalizer
from smart_kit.utils.picklable_mock import PicklableMock


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def patch_get_app_config(mock_get_app_config):
    result = PicklableMock()
    sk_path = os.path.dirname(smart_kit.__file__)
    result.STATIC_PATH = os.path.join(sk_path, 'template/static')
    mock_get_app_config.return_value = result
    result.NORMALIZER = LocalTextNormalizer()
    result.ENVIRONMENT = "ift"
    mock_get_app_config.return_value = result


class MockRequirement:
    def __init__(self, items=None):
        items = items or {}
        self.cond = items.get("cond") or False

    async def check(self, text_preprocessing_result, user, params):
        return self.cond


class MockTextNormalizationResult:
    def __init__(self, normalized=None, number_of_numbers=None, currencies_number=None, tokens=None):
        number_of_numbers = number_of_numbers or 0
        currencies_number = currencies_number or 0
        if normalized:
            self.words_tokenized = list(token.get("text") for token in normalized)
            self.words_tokenized_set = set(self.words_tokenized)
        else:
            self.words_tokenized = list()
            self.words_tokenized_set = set()
        self.number_of_numbers = number_of_numbers
        self.currencies_number = currencies_number
        self.tokenized_elements_list = tokens


class MockAmountOperator:
    def __init__(self, items):
        self.amount = items["amount"]

    def compare(self, value):
        return value > self.amount


class MockOperator:
    def __init__(self, amount):
        self.amount = amount

    def compare(self, value):
        return value > self.amount


class EQMockOperator:
    def __init__(self, amount):
        self.amount = amount

    def compare(self, value):
        return value == self.amount


class RequirementTest(unittest.IsolatedAsyncioTestCase):
    async def test_base(self):
        requirement = Requirement(None)
        assert await requirement.check(None, None)

    async def test_composite(self):
        registered_factories[Requirement] = MockRequirement
        requirement = CompositeRequirement({"requirements": [
            {"cond": True},
            {"cond": True}
        ]})
        self.assertTrue(await requirement.check(None, None))

    async def test_and_success(self):
        registered_factories[Requirement] = MockRequirement
        requirement = AndRequirement({"requirements": [
            {"cond": True},
            {"cond": True}
        ]})
        self.assertTrue(await requirement.check(None, None))

    async def test_and_fail(self):
        registered_factories[Requirement] = MockRequirement
        requirement = AndRequirement({"requirements": [
            {"cond": True},
            {"cond": False}
        ]})
        self.assertFalse(await requirement.check(None, None))

    async def test_or_success(self):
        registered_factories[Requirement] = MockRequirement
        requirement = OrRequirement({"requirements": [
            {"cond": True},
            {"cond": False}
        ]})
        self.assertTrue(await requirement.check(None, None))

    async def test_or_fail(self):
        registered_factories[Requirement] = MockRequirement
        requirement = OrRequirement({"requirements": [
            {"cond": False},
            {"cond": False}
        ]})
        self.assertFalse(await requirement.check(None, None))

    async def test_not_success(self):
        registered_factories[Requirement] = MockRequirement
        requirement = NotRequirement({"requirement": {"cond": False}})
        self.assertTrue(await requirement.check(None, None))

    async def test_not_fail(self):
        registered_factories[Requirement] = MockRequirement
        requirement = NotRequirement({"requirement": {"cond": True}})
        self.assertFalse(await requirement.check(None, None))

    async def test_channel_success(self):
        user = PicklableMock()
        message = Mock(channel="ch1")
        user.message = message
        requirement = ChannelRequirement({"channels": ["ch1"]})
        text_normalization_result = None
        self.assertTrue(await requirement.check(text_normalization_result, user))

    async def test_channel_fail(self):
        user = PicklableMock()
        message = Mock(channel="ch2")
        user.message = message
        requirement = ChannelRequirement({"channels": ["ch1"]})
        text_normalization_result = None
        self.assertFalse(await requirement.check(text_normalization_result, user))

    async def test_random_requirement_true(self):
        requirement = RandomRequirement({"percent": 100})
        self.assertTrue(await requirement.check(None, None))

    async def test_random_requirement_false(self):
        requirement = RandomRequirement({"percent": 0})
        self.assertFalse(await requirement.check(None, None))

    async def test_topic_requirement(self):
        requirement = TopicRequirement({"topics": ["test"]})
        user = PicklableMock()
        message = PicklableMock()
        message.topic_key = "test"
        user.message = message
        self.assertTrue(await requirement.check(None, user))

    async def test_counter_value_requirement(self):
        registered_factories[Operator] = MockAmountOperator
        user = PicklableMock()
        counter = PicklableMock()
        counter.__gt__ = Mock(return_value=True)
        user.counters = {"test": counter}
        requirement = CounterValueRequirement({"operator": {"type": "equal", "amount": 2}, "key": "test"})
        self.assertTrue(await requirement.check(None, user))

    async def test_counter_time_requirement(self):
        registered_factories[Operator] = MockAmountOperator
        user = PicklableMock()
        counter = PicklableMock()
        counter.update_time = int(time()) - 10
        user.counters = {"test": counter}
        requirement = CounterUpdateTimeRequirement({"operator": {"type": "more_or_equal", "amount": 5}, "key": "test"})
        self.assertTrue(await requirement.check(None, user))

    async def test_template_req_true(self):
        items = {
            "template": "{{ payload.message.strip() in payload.murexIds }}"
        }
        requirement = TemplateRequirement(items)
        params = {"payload": {
            "groupCode": "BROKER",
            "murexIds": ["AAA", "BBB"],
            "message": " BBB    "
        }}
        user = PicklableMock()
        user.parametrizer = PicklableMock()
        user.parametrizer.collect = Mock(return_value=params)
        self.assertTrue(await requirement.check(None, user))

    async def test_template_req_false(self):
        items = {
            "template": "{{ payload.groupCode == 'BROKER' }}"
        }
        requirement = TemplateRequirement(items)
        params = {"payload": {"groupCode": "BROKER1"}}
        user = PicklableMock()
        user.parametrizer = PicklableMock()
        user.parametrizer.collect = Mock(return_value=params)
        self.assertFalse(await requirement.check(None, user))

    async def test_template_req_raise(self):
        items = {
            "template": "{{ payload.groupCode }}"
        }
        requirement = TemplateRequirement(items)
        params = {"payload": {"groupCode": "BROKER1"}}
        user = PicklableMock()
        user.parametrizer = PicklableMock()
        user.parametrizer.collect = Mock(return_value=params)
        self.assertRaises(TypeError, _run, requirement.check, None, user)

    async def test_rolling_requirement_true(self):
        user = PicklableMock()
        user.id = "353454"
        requirement = RollingRequirement({"percent": 100})
        text_normalization_result = None
        self.assertTrue(await requirement.check(text_normalization_result, user))

    async def test_rolling_requirement_false(self):
        user = PicklableMock()
        user.id = "353454"
        requirement = RollingRequirement({"percent": 0})
        text_normalization_result = None
        self.assertFalse(await requirement.check(text_normalization_result, user))

    async def test_time_requirement_true(self):
        user = PicklableMock()
        user.id = "353454"
        user.message.payload = {
            "meta": {
                "time": {
                    "timestamp": 1610990255000,  # ~ 2021-01-18 17:17:35
                    "timezone_offset_sec": 1000000000,  # shouldn't affect
                }
            }
        }
        requirement = TimeRequirement(
            {
                "operator": {
                    "type": "more",
                    "amount": "17:00:00",
                }
            }
        )
        text_normalization_result = None
        self.assertTrue(await requirement.check(text_normalization_result, user))

    async def test_time_requirement_false(self):
        user = PicklableMock()
        user.id = "353454"
        user.message.payload = {
            "meta": {
                "time": {
                    "timestamp": 1610979455663,  # ~ 2021-01-18 17:17:35
                    "timezone_offset_sec": 1000000000,  # shouldn't affect
                }
            }
        }
        requirement = TimeRequirement(
            {
                "operator": {
                    "type": "more",
                    "amount": "18:00:00",
                }
            }
        )
        text_normalization_result = None
        self.assertFalse(await requirement.check(text_normalization_result, user))

    async def test_datetime_requirement_true(self):
        user = PicklableMock()
        user.id = "353454"
        user.message.payload = {
            "meta": {
                "time": {
                    "timestamp": 1610979455663,  # ~ 2021-01-18 17:17:35
                    "timezone_offset_sec": 1000000000,  # shouldn't affect
                }
            }
        }
        requirement = DateTimeRequirement(
            {
                "match_cron": "*/17 14-19 * * mon"
            }
        )
        text_normalization_result = None
        self.assertTrue(await requirement.check(text_normalization_result, user))

    async def test_datetime_requirement_false(self):
        user = PicklableMock()
        user.id = "353454"
        user.message.payload = {
            "meta": {
                "time": {
                    "timestamp": 1610979455663,  # ~ 2021-01-18 17:17:35
                    "timezone_offset_sec": 1000000000,  # shouldn't affect
                }
            }
        }
        requirement = DateTimeRequirement(
            {
                "match_cron": "* * * * 6,7"
            }
        )
        text_normalization_result = None
        self.assertFalse(await requirement.check(text_normalization_result, user))

    @patch('smart_kit.configs.get_app_config')
    async def test_intersection_requirement_true(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config)
        user = PicklableMock()
        requirement = IntersectionRequirement(
            {
                "phrases": [
                    'да',
                    'давай',
                    'хочу',
                ]
            }
        )
        text_normalization_result = PicklableMock()
        text_normalization_result.tokenized_elements_list_pymorphy = [
            {'lemma': 'я'},
            {'lemma': 'хотеть'},
        ]
        self.assertTrue(await requirement.check(text_normalization_result, user))

    @patch('smart_kit.configs.get_app_config')
    async def test_intersection_requirement_false(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config)
        user = PicklableMock()
        requirement = IntersectionRequirement(
            {
                "phrases": [
                    'да',
                    'давай',
                    'хочу',
                ]
            }
        )
        text_normalization_result = PicklableMock()
        text_normalization_result.tokenized_elements_list_pymorphy = [
            {'lemma': 'ни'},
            {'lemma': 'за'},
            {'lemma': 'что'},
        ]
        self.assertFalse(await requirement.check(text_normalization_result, user))

    @patch.object(ExternalClassifier, "find_best_answer", return_value=[{"answer": "нет", "score": 1.0, "other": False}])
    async def test_classifier_requirement_true(self, mock_classifier_model):
        """Тест кейз проверяет что условие возвращает True, если результат классификации запроса относится к одной
        из указанных категорий, прошедших порог, но не равной классу other.
        """
        test_items = {"type": "classifier", "classifier": {"type": "external", "classifier": "hello_scenario_classifier"}}
        classifier_requirement = ClassifierRequirement(test_items)
        mock_user = PicklableMock()
        mock_user.descriptions = {"external_classifiers": ["read_book_or_not_classifier", "hello_scenario_classifier"]}
        result = await classifier_requirement.check(PicklableMock(), mock_user)
        self.assertTrue(result)

    @patch.object(ExternalClassifier, "find_best_answer", return_value=[])
    async def test_classifier_requirement_false(self, mock_classifier_model):
        """Тест кейз проверяет что условие возвращает False, если модель классификации не вернула ответ."""
        test_items = {"type": "classifier", "classifier": {"type": "external", "classifier": "hello_scenario_classifier"}}
        classifier_requirement = ClassifierRequirement(test_items)
        mock_user = PicklableMock()
        mock_user.descriptions = {"external_classifiers": ["read_book_or_not_classifier", "hello_scenario_classifier"]}
        result = await classifier_requirement.check(PicklableMock(), mock_user)
        self.assertFalse(result)

    @patch.object(ExternalClassifier, "find_best_answer", return_value=[{"answer": "other", "score": 1.0, "other": True}])
    async def test_classifier_requirement_false_if_class_other(self, mock_classifier_model):
        """Тест кейз проверяет что условие возвращает False, если наиболее вероятный вариант есть класс other."""
        test_items = {"type": "classifier", "classifier": {"type": "external", "classifier": "hello_scenario_classifier"}}
        classifier_requirement = ClassifierRequirement(test_items)
        mock_user = PicklableMock()
        mock_user.descriptions = {"external_classifiers": ["read_book_or_not_classifier", "hello_scenario_classifier"]}
        result = await classifier_requirement.check(PicklableMock(), mock_user)
        self.assertFalse(result)

    async def test_form_field_value_requirement_true(self):
        """Тест кейз проверяет что условие возвращает True, т.к в
        форме form_name в поле form_field значение совпадает с переданным field_value.
        """
        form_name = "test_form"
        form_field = "test_field"
        field_value = "test_value"

        test_itmes = {"form_name": form_name, "field_name": form_field, "value": field_value}
        req_form_field_value = FormFieldValueRequirement(test_itmes)

        user = PicklableMock()
        user.forms = {form_name: PicklableMock()}
        user.forms[form_name].fields = {form_field: PicklableMock(), "value": field_value}
        user.forms[form_name].fields[form_field].value = field_value

        result = await req_form_field_value.check(PicklableMock(), user)
        self.assertTrue(result)

    async def test_form_field_value_requirement_false(self):
        """Тест кейз проверяет что условие возвращает False, т.к в
        форме form_name в поле form_field значение НЕ совпадает с переданным field_value.
        """
        form_name = "test_form"
        form_field = "test_field"
        field_value = "test_value"

        test_itmes = {"form_name": form_name, "field_name": form_field, "value": field_value}
        req_form_field_value = FormFieldValueRequirement(test_itmes)

        user = PicklableMock()
        user.forms = {form_name: PicklableMock()}
        user.forms[form_name].fields = {form_field: PicklableMock(), "value": "OTHER_TEST_VAL"}
        user.forms[form_name].fields[form_field].value = "OTHER_TEST_VAL"

        result = await req_form_field_value.check(PicklableMock(), user)
        self.assertFalse(result)

    @patch("smart_kit.configs.get_app_config")
    async def test_environment_requirement_true(self, mock_get_app_config):
        """Тест кейз проверяет что условие возвращает True, т.к среда исполнения из числа values."""
        patch_get_app_config(mock_get_app_config)
        environment_req = EnvironmentRequirement({"values": ["ift", "uat"]})
        self.assertTrue(await environment_req.check(PicklableMock(), PicklableMock()))

    @patch("smart_kit.configs.get_app_config")
    async def test_environment_requirement_false(self, mock_get_app_config):
        """Тест кейз проверяет что условие возвращает False, т.к среда исполнения НЕ из числа values."""
        patch_get_app_config(mock_get_app_config)
        environment_req = EnvironmentRequirement({"values": ["uat", "pt"]})
        self.assertFalse(await environment_req.check(PicklableMock(), PicklableMock()))

    async def test_any_substring_in_lowered_text_requirement_true(self):
        """Тест кейз проверяет что условие возвращает True, т.к нашлась подстрока из списка substrings, которая
        встречается в оригинальном тексте в нижнем регистре.
        """
        req = AnySubstringInLoweredTextRequirement({"substrings": ["искомая подстрока", "другое знанчение"]})
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.raw = {"original_text": "КАКОЙ-ТО ТЕКСТ С ИСКОМАЯ ПОДСТРОКА"}
        result = await req.check(text_preprocessing_result, PicklableMock())
        self.assertTrue(result)

    async def test_any_substring_in_lowered_text_requirement_false(self):
        """Тест кейз проверяет что условие возвращает False, т.к НЕ нашлась ни одна подстрока из списка substrings,
        которая бы встречалась в оригинальном тексте в нижнем регистре.
        """
        req = AnySubstringInLoweredTextRequirement({"substrings": ["искомая подстрока", "другая подстрока"]})
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.raw = {"original_text": "КАКОЙ-ТО ТЕКСТ"}
        result = await req.check(text_preprocessing_result, PicklableMock())
        self.assertFalse(result)

    async def test_num_in_range_requirement_true(self):
        """Тест кейз проверяет что условие возвращает True, т.к число находится в заданном диапазоне."""
        req = NumInRangeRequirement({"min_num": "5", "max_num": "10"})
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.num_token_values = 7
        self.assertTrue(await req.check(text_preprocessing_result, PicklableMock()))

    async def test_num_in_range_requirement_false(self):
        """Тест кейз проверяет что условие возвращает False, т.к число НЕ находится в заданном диапазоне."""
        req = NumInRangeRequirement({"min_num": "5", "max_num": "10"})
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.num_token_values = 20
        self.assertFalse(await req.check(text_preprocessing_result, PicklableMock()))

    async def test_phone_number_number_requirement_true(self):
        """Тест кейз проверяет что условие возвращает True, т.к кол-во номеров телефонов больше заданного."""
        req = PhoneNumberNumberRequirement({"operator": {"type": "more", "amount": 1}})
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.get_token_values_by_type.return_value = ["89030478799", "89092534523"]
        self.assertTrue(await req.check(text_preprocessing_result, PicklableMock()))

    async def test_phone_number_number_requirement_false(self):
        """Тест кейз проверяет что условие возвращает False, т.к кол-во номеров телефонов НЕ больше заданного."""
        req = PhoneNumberNumberRequirement({"operator": {"type": "more", "amount": 10}})
        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.get_token_values_by_type.return_value = ["89030478799"]
        self.assertFalse(await req.check(text_preprocessing_result, PicklableMock()))

    @patch("smart_kit.configs.get_app_config")
    async def test_intersection_with_tokens_requirement_true(self, mock_get_app_config):
        """Тест кейз проверяет что условие возвращает True, т.к хотя бы одно слово из нормализованного
        вида запроса входит в список слов input_words.
        """
        patch_get_app_config(mock_get_app_config)

        req = IntersectionWithTokensSetRequirement({"input_words": ["погода", "время"]})

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.raw = {"tokenized_elements_list_pymorphy": [
            {"text": "прогноз", "grammem_info": {
                "animacy": "inan", "case": "acc", "gender": "masc", "number": "sing", "raw_gram_info":
                    "animacy=inan|case=acc|gender=masc|number=sing", "part_of_speech": "NOUN"}, "lemma": "прогноз"},
            {"text": "погоды", "grammem_info": {
                "animacy": "inan", "case": "gen", "gender": "fem", "number": "sing",
                "raw_gram_info": "animacy=inan|case=gen|gender=fem|number=sing",
                "part_of_speech": "NOUN"}, "lemma": "погода"}
            ]}

        self.assertTrue(await req.check(text_preprocessing_result, PicklableMock()))

    @patch("smart_kit.configs.get_app_config")
    async def test_intersection_with_tokens_requirement_false(self, mock_get_app_config):
        """Тест кейз проверяет что условие возвращает False, т.к ни одно слово из нормализованного
        вида запроса не входит в список слов input_words.
        """
        patch_get_app_config(mock_get_app_config)

        req = IntersectionWithTokensSetRequirement({"input_words": ["время"]})

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.raw = {"tokenized_elements_list_pymorphy": [
            {"text": "прогноз", "grammem_info": {
                "animacy": "inan", "case": "acc", "gender": "masc", "number": "sing", "raw_gram_info":
                    "animacy=inan|case=acc|gender=masc|number=sing", "part_of_speech": "NOUN"}, "lemma": "прогноз"},
            {"text": "погоды", "grammem_info": {
                "animacy": "inan", "case": "gen", "gender": "fem", "number": "sing",
                "raw_gram_info": "animacy=inan|case=gen|gender=fem|number=sing",
                "part_of_speech": "NOUN"}, "lemma": "погода"}
        ]}

        self.assertFalse(await req.check(text_preprocessing_result, PicklableMock()))

    @patch("smart_kit.configs.get_app_config")
    async def test_normalized_text_in_set_requirement_true(self, mock_get_app_config):
        """Тест кейз проверяет что условие возвращает True, т.к в нормализованном представлении
        запрос полностью совпадает с одной из нормализованных строк из input_words.
        """
        patch_get_app_config(mock_get_app_config)

        req = NormalizedTextInSetRequirement({"input_words": ["погода", "время"]})

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.raw = {"normalized_text": "погода ."}

        self.assertTrue(await req.check(text_preprocessing_result, PicklableMock()))

    @patch("smart_kit.configs.get_app_config")
    async def test_normalized_text_in_set_requirement_false(self, mock_get_app_config):
        """Тест кейз проверяет что условие возвращает False, т.к в нормализованном представлении
        запрос НЕ совпадает ни с одной из нормализованных строк из input_words.
        """
        patch_get_app_config(mock_get_app_config)

        req = NormalizedTextInSetRequirement({"input_words": ["погода", "время"]})

        text_preprocessing_result = PicklableMock()
        text_preprocessing_result.raw = {"normalized_text": "хотеть узнать ."}

        self.assertFalse(await req.check(text_preprocessing_result, PicklableMock()))

    async def test_character_id_requirement_true(self):
        req = CharacterIdRequirement({"values": ["sber", "afina"]})
        user = Mock()
        user.message = Mock()
        user.message.payload = {"character": {"id": "sber", "name": "Сбер", "gender": "male"}}
        self.assertTrue(await req.check(Mock(), user))

    async def test_character_id_requirement_false(self):
        req = CharacterIdRequirement({"values": ["afina"]})
        user = Mock()
        user.message = Mock()
        user.message.payload = {"character": {"id": "sber", "name": "Сбер", "gender": "male"}}
        self.assertFalse(await req.check(Mock(), user))

    async def test_feature_toggle_check_requirement_true(self):
        req = FeatureToggleRequirement({"toggle_name": "test_true_toggle_name"})
        mock_user = Mock()
        mock_user.settings = {"template_settings": {"test_true_toggle_name": True}}
        self.assertTrue(await req.check(Mock(), mock_user))

    async def test_feature_toggle_check_requirement_false(self):
        req = FeatureToggleRequirement({"toggle_name": "test_false_toggle_name"})
        mock_user = Mock()
        mock_user.settings = {"template_settings": {"test_false_toggle_name": False}}
        self.assertFalse(await req.check(Mock(), mock_user))


if __name__ == '__main__':
    unittest.main()
