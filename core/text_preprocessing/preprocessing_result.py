import nltk

from collections import defaultdict
from core.text_preprocessing.grammem.grammem_constants import TOKEN_VALUE, TOKEN_TYPE, IS_BEGINNING_OF_COMPOSITE, \
    COMPOSITE_TOKEN_VALUE, COMPOSITE_TOKEN_TYPE, VALUE, LIST_OF_TOKEN_TYPES_DATA
from core.text_preprocessing.helpers import TokenizeHelper
from core.text_preprocessing.constants import NUM_TOKEN, CCY_TOKEN, PERSON_TOKEN, MONEY_TOKEN, TIME_DATE_TOKEN, \
    PERIOD_TOKEN, TIME_DATE_INTERVAL_TOKEN, RELATIVE_TIME_TOKEN, ORG_TOKEN, GEO_TOKEN, TIME_TIME_TOKEN, \
    SENTENCE_ENDPOINT_TOKEN
from core.text_preprocessing.base import BaseTextPreprocessingResult


class TextPreprocessingResult(BaseTextPreprocessingResult):
    __slots__ = ("original_text", "normalized_text", "original_message_name", "__tokenized_elements_list",
                 "_tokenized_string", "_normalized_text_with_verb_mood", "_words_tokenized", "_words_tokenized_set",
                 "_num_token_values", "_person_token_values", "_money_token_values", "_time_date_token_values",
                 "_period_token_values", "_org_token_values", "_time_date_interval_token_values",
                 "_relative_token_values", "_ccy_token_values", "_geo_token_values", "pipeline_results",
                 "_tokenized_string_stop_words", "_words_tokenized_stop_words", "_words_tokenized_set_stop_words")

    def __init__(self, items):
        super(TextPreprocessingResult, self).__init__(items)
        self.original_text = items.get("original_text", "")
        self.normalized_text = items.get("normalized_text", "")
        self.original_message_name = items.get("original_message_name", "")
        self.__tokenized_elements_list = items.get("tokenized_elements_list", [])
        self.pipeline_results = items.get("pipeline_results", {})
        self._human_normalized_text = items.get("human_normalized_text")
        self._human_normalized_text_with_anaphora = items.get("human_normalized_text_with_anaphora")
        self._tokenized_elements_list_pymorphy = None
        self._normalized_text_pymorphy = None
        self._tokenized_string = None
        self._normalized_text_with_verb_mood = None
        self._words_tokenized = None
        self._words_tokenized_set = None
        self._num_token_values = None
        self._person_token_values = None
        self._money_token_values = None
        self._time_date_token_values = None
        self._period_token_values = None
        self._org_token_values = None
        self._geo_token_values = None
        self._time_time_token_values = None
        self._time_date_interval_token_values = None
        self._relative_token_values = None
        self._ccy_token_values = None
        self._tokenized_string_stop_words = None
        self._words_tokenized_stop_words = None
        self._words_tokenized_set_stop_words = None

    @property
    def tokenized_elements_list_pymorphy(self):
        if self._tokenized_elements_list_pymorphy is None:

            from smart_kit.configs import get_app_config
            app_config = get_app_config()

            self._tokenized_elements_list_pymorphy = app_config.NORMALIZER(self.original_text)["tokenized_elements_list"]

        return self._tokenized_elements_list_pymorphy

    @property
    def normalized_text_pymorphy(self):
        if self._normalized_text_pymorphy is None:

            from smart_kit.configs import get_app_config
            app_config = get_app_config()

            normalized_words = [app_config.NORMALIZER.morph.pymorphy_analyzer.parse(tokenized_word)[0].normalized.normal_form
                                for tokenized_word in nltk.tokenize.word_tokenize(self.original_text)]
            self._normalized_text_pymorphy = " ".join(normalized_words)

        return self._normalized_text_pymorphy

    @property
    def tokenized_string(self):
        if self._tokenized_string is None:
            self._tokenized_string = TokenizeHelper.return_lemmas_only(self.__tokenized_elements_list,
                                                                       include_sentence_endpoint=False)
        return self._tokenized_string

    @property
    def tokenized_string_stop_words(self):
        if self._tokenized_string_stop_words is None:
            self._tokenized_string_stop_words = TokenizeHelper.return_lemmas_only(self.__tokenized_elements_list,
                                                                                  include_sentence_endpoint=False,
                                                                                  consider_stop_words=True)
        return self._tokenized_string_stop_words

    @property
    def human_normalized_text(self):
        if self._human_normalized_text is None:
            self._human_normalized_text = TokenizeHelper.get_human_normalized_text(self.__tokenized_elements_list)
        return self._human_normalized_text

    @property
    def human_normalized_text_with_anaphora(self):
        if self._human_normalized_text_with_anaphora is None:
            self._human_normalized_text_with_anaphora = \
                TokenizeHelper.get_human_normalized_text_with_anaphora(self.__tokenized_elements_list)
        return self._human_normalized_text_with_anaphora

    @property
    def normalized_text_with_verb_mood(self):
        if self._normalized_text_with_verb_mood is None:
            self._normalized_text_with_verb_mood = TokenizeHelper.return_lemmas_only(self.__tokenized_elements_list,
                                                                                     include_sentence_endpoint=True,
                                                                                     show_verb_mood=True)
        return self._normalized_text_with_verb_mood

    @property
    def words_tokenized(self):
        if self._words_tokenized is None:
            self._words_tokenized = self.tokenized_string.split(" ")
        return self._words_tokenized

    @property
    def words_tokenized_stop_words(self):
        if self._words_tokenized_stop_words is None:
            self._words_tokenized_stop_words = self.tokenized_string_stop_words.split(" ")
        return self._words_tokenized_stop_words

    @property
    def words_tokenized_set(self):
        if self._words_tokenized_set is None:
            self._words_tokenized_set = set(self.words_tokenized)
        return self._words_tokenized_set

    @property
    def words_tokenized_set_stop_words(self):
        if self._words_tokenized_set_stop_words is None:
            self._words_tokenized_set_stop_words = set(self.words_tokenized_stop_words)
        return self._words_tokenized_set_stop_words

    @property
    def all_token_values(self):
        result = defaultdict(list)
        for token in self.__tokenized_elements_list:
            for token_option in token.get(LIST_OF_TOKEN_TYPES_DATA, []):
                if token_option[TOKEN_TYPE] != SENTENCE_ENDPOINT_TOKEN:
                    result[token_option[TOKEN_TYPE]].append(token_option[TOKEN_VALUE])
            if token.get(IS_BEGINNING_OF_COMPOSITE):
                result[token.get(COMPOSITE_TOKEN_TYPE)].append(token.get(COMPOSITE_TOKEN_VALUE))
        return result

    def get_token_values_by_type(self, token_type):
        final_list = []
        for t in self.__tokenized_elements_list:
            list_of_values = t.get(LIST_OF_TOKEN_TYPES_DATA, [])
            for values_dicti in list_of_values:
                if values_dicti[TOKEN_TYPE] == token_type:
                    final_list.append(values_dicti.get(TOKEN_VALUE, {}).get(VALUE))
        return final_list

    def get_composite_token_values_by_type(self, composite_token_type):
        list_of_composite_token_values = []
        for token in self.__tokenized_elements_list:
            if token.get(COMPOSITE_TOKEN_TYPE) == composite_token_type and token.get(IS_BEGINNING_OF_COMPOSITE):
                list_of_composite_token_values.append(token.get(COMPOSITE_TOKEN_VALUE))
        return list_of_composite_token_values

    @property
    def num_token_values(self):
        if self._num_token_values is None:
            self._num_token_values = self.get_token_values_by_type(NUM_TOKEN)
        return self._num_token_values

    @property
    def person_token_values(self):
        if self._person_token_values is None:
            self._person_token_values = self.get_composite_token_values_by_type(PERSON_TOKEN)
        return self._person_token_values

    @property
    def money_token_values(self):
        if self._money_token_values is None:
            self._money_token_values = self.get_composite_token_values_by_type(MONEY_TOKEN)
        return self._money_token_values

    @property
    def time_date_token_values(self):
        if self._time_date_token_values is None:
            self._time_date_token_values = self.get_composite_token_values_by_type(TIME_DATE_TOKEN)
        return self._time_date_token_values

    @property
    def period_token_values(self):
        if self._period_token_values is None:
            self._period_token_values = self.get_composite_token_values_by_type(PERIOD_TOKEN)
        return self._period_token_values

    @property
    def org_token_values(self):
        if self._org_token_values is None:
            self._org_token_values = self.get_composite_token_values_by_type(ORG_TOKEN)
        return self._org_token_values

    @property
    def geo_token_values(self):
        if self._geo_token_values is None:
            self._geo_token_values = self.get_composite_token_values_by_type(GEO_TOKEN)
        return self._geo_token_values

    @property
    def time_date_interval_token_values(self):
        if self._time_date_interval_token_values is None:
            self._time_date_interval_token_values = self.get_composite_token_values_by_type(TIME_DATE_INTERVAL_TOKEN)
        return self._time_date_interval_token_values

    @property
    def time_time_token_values(self):
        if self._time_time_token_values is None:
            self._time_time_token_values = self.get_composite_token_values_by_type(TIME_TIME_TOKEN)
        return self._time_time_token_values

    @property
    def relative_token_values(self):
        if self._relative_token_values is None:
            self._relative_token_values = self.get_composite_token_values_by_type(RELATIVE_TIME_TOKEN)
        return self._relative_token_values

    @property
    def number_of_numbers(self):
        return len(self.num_token_values)

    @property
    def ccy_token_values(self):
        if self._ccy_token_values is None:
            self._ccy_token_values = self.get_token_values_by_type(CCY_TOKEN)
        return self._ccy_token_values

    @property
    def currencies_number(self):
        return len(self.ccy_token_values)

    @property
    def tokenized_elements_list(self):
        return self.__tokenized_elements_list

    @property
    def raw(self):
        return {"original_text": self.original_text,
                "normalized_text": self.normalized_text,
                "tokenized_elements_list": self.__tokenized_elements_list}
