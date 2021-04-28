"""Requirements на текст запроса пользователя."""

from typing import Optional, Dict, Any

from core.basic_models.requirement.basic_requirements import Requirement, ComparisonRequirement
from core.logging.logger_utils import log
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.text_preprocessing.helpers import TokenizeHelper


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


class TokensNumRequirement(ComparisonRequirement):
    """Условие возвращает True, если попадает под ограничение на длину запроса в количестве слов, иначе - False."""

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        num_tokens = TokenizeHelper.num_tokens(text_preprocessing_result)
        result = self.operator.compare(num_tokens)
        if result:
            params = self._log_params()
            params["num_tokens"] = num_tokens
            message = "Requirement: %(requirement)s, num_tokens: %(num_tokens)s"
            log(message, user, params)
        return result


class NormalizedTokensRequirement(Requirement):

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(NormalizedTokensRequirement, self).__init__(items, id)
        # Получаем используемый нормализатор из конфига аппа
        from smart_kit.configs import get_app_config
        app_config = get_app_config()
        self.normalizer = app_config.NORMALIZER
        # Нормализуем слова из symbols
        self.symbols = set(items["symbols"])
        normalized_input_symbols = [
            norm_res["normalized_text"] for norm_res in self.normalizer.normalize_sequence(self.symbols)]
        self.normalized_input_symbols = set(normalized_input_symbols)


class IntersectionWithTokensSetRequirement(NormalizedTokensRequirement):
    """Условие возвращает True, если хотя бы одно слово из нормализованного вида запроса входит
    в список слов symbols, иначе - False.
    Слова из symbols также проходят нормализацию перед сравнением.
    """

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        normalized_text_tokens = [
            token["lemma"] for token in text_preprocessing_result.raw["tokenized_elements_list"]
            if not token["token_type"] == "SENTENCE_ENDPOINT_TOKEN"
        ]
        normalized_text_tokens = set(normalized_text_tokens)
        result = bool(self.normalized_input_symbols.intersection(normalized_text_tokens))
        if result:
            params = self._log_params()
            params["normalized_symbols"] = self.normalized_input_symbols
            params["words_normalized_set"] = normalized_text_tokens
            message = "Requirement: %(requirement)s, normalized_symbols: %(normalized_symbols)s, " \
                      "words_normalized_set: %(words_normalized_set)s"
            log(message, user, params)
        return result
