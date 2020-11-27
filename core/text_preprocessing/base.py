class BaseTextPreprocessingResult:

    def __init__(self, items):
        pass

    @property
    def tokenized_string(self):
        return NotImplementedError

    @property
    def tokenized_string_stop_words(self):
        return NotImplementedError

    @property
    def normalized_text_with_verb_mood(self):
        return NotImplementedError

    @property
    def words_tokenized(self):
        return NotImplementedError

    @property
    def words_tokenized_stop_words(self):
        return NotImplementedError

    @property
    def words_tokenized_set(self):
        return NotImplementedError

    @property
    def words_tokenized_set_stop_words(self):
        return NotImplementedError

    def get_token_values_by_type(self, token_type):
        return NotImplementedError

    def get_composite_token_values_by_type(self, composite_token_type):
        return NotImplementedError

    @property
    def num_token_values(self):
        return NotImplementedError

    @property
    def person_token_values(self):
        return NotImplementedError

    @property
    def money_token_values(self):
        return NotImplementedError

    @property
    def time_date_token_values(self):
        return NotImplementedError

    @property
    def period_token_values(self):
        return NotImplementedError

    @property
    def org_token_values(self):
        return NotImplementedError

    @property
    def geo_token_values(self):
        return NotImplementedError

    @property
    def time_date_interval_token_values(self):
        return NotImplementedError

    @property
    def time_time_token_values(self):
        return NotImplementedError

    @property
    def relative_token_values(self):
        return NotImplementedError

    @property
    def number_of_numbers(self):
        return NotImplementedError

    @property
    def ccy_token_values(self):
        return NotImplementedError

    @property
    def currencies_number(self):
        return NotImplementedError

    @property
    def tokenized_elements_list(self):
        return NotImplementedError

    @property
    def raw(self):
        return NotImplementedError
