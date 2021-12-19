"""Requirements на текст запроса пользователя."""

from typing import Optional, Dict, Any

from core.basic_models.requirement.basic_requirements import Requirement, ComparisonRequirement
from core.logging.logger_utils import log
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult
from scenarios.user.user_model import User


class AnySubstringInLoweredTextRequirement(Requirement):
    """Условие возвращает True, если хотя бы одна подстрока из списка substrings встречается
    в оригинальном тексте в нижнем регистре, иначе - False.
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(AnySubstringInLoweredTextRequirement, self).__init__(items, id)
        self.substrings = self.items["substrings"]

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        lowered_text = text_preprocessing_result.lower() if isinstance(text_preprocessing_result, str) \
            else text_preprocessing_result.raw["original_text"].lower()
        return any(s.lower() in lowered_text for s in self.substrings)


class NormalizedInputWordsRequirement(Requirement):

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(NormalizedInputWordsRequirement, self).__init__(items, id)

        # Получаем используемый нормализатор из конфига аппа
        from smart_kit.configs import get_app_config
        app_config = get_app_config()
        self.normalizer = app_config.NORMALIZER

        # Нормализуем входные слова из условия
        self.input_words = set(items["input_words"])
        self.normalized_input_words = set([
            norm_res["normalized_text"].replace(".", "").strip()
            for norm_res in self.normalizer.normalize_sequence(list(self.input_words))
        ])


class IntersectionWithTokensSetRequirement(NormalizedInputWordsRequirement):
    """Условие возвращает True, если хотя бы одно слово из нормализованного вида запроса входит
    в список слов input_words, иначе - False.
    Слова из input_words также проходят нормализацию перед сравнением.
    """

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        words_normalized_set = set([
            token["lemma"] for token in text_preprocessing_result.raw["tokenized_elements_list_pymorphy"]
            if not token.get("token_type") == "SENTENCE_ENDPOINT_TOKEN"
        ])
        result = bool(self.normalized_input_words.intersection(words_normalized_set))
        if result:
            params = self._log_params()
            params["normalized_input_words"] = self.normalized_input_words
            params["words_normalized_set"] = words_normalized_set
            message = "Requirement: %(requirement)s, normalized_input_words: %(normalized_input_words)s, " \
                      "words_normalized_set: %(words_normalized_set)s"
            log(message, user, params)
        return result


class NormalizedTextInSetRequirement(NormalizedInputWordsRequirement):
    """Условие возвращает True, если в нормализованном представлении запрос полностью совпадает с одной из
    нормализованных строк из input_words, иначе - False.
    """

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        normalized_text = text_preprocessing_result.raw["normalized_text"].replace(".", "").strip()
        result = normalized_text in self.normalized_input_words
        if result:
            params = self._log_params()
            params["normalized_text"] = normalized_text
            params["normalized_input_words"] = self.normalized_input_words
            message = "Requirement: %(requirement)s, normalized_text: %(normalized_text)s, " \
                      "normalized_input_words: %(normalized_input_words)s"
            log(message, user, params)

        return result


class PhoneNumberNumberRequirement(ComparisonRequirement):
    """Условие возвращает True, если кол-во номеров телефонов больше/меньше/.. X, иначе - False.
    Строго говоря, считается кол-во токенов, имеющих token_type = "PHONE_NUMBER_TOKEN".
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        len_phone_number_token = len(text_preprocessing_result.get_token_values_by_type("PHONE_NUMBER_TOKEN"))
        result = self.operator.compare(len_phone_number_token)
        if result:
            params = self._log_params()
            params["len_phone_number_token"] = len_phone_number_token
            message = "Requirement: %(requirement)s, len_phone_number_token: %(len_phone_number_token)s"
            log(message, user, params)
        return result


class NumInRangeRequirement(Requirement):
    """Условие возвращает True, если число находится в заданном диапазоне, иначе - False."""

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(NumInRangeRequirement, self).__init__(items, id)
        self.min_num = float(items["min_num"])
        self.max_num = float(items["max_num"])

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
              params: Dict[str, Any] = None) -> bool:
        num = float(text_preprocessing_result.num_token_values)
        return self.min_num <= num <= self.max_num if num else False
