from lazy import lazy

from core.basic_models.parametrizers.filter import Filter


class BasicParametrizer:
    def __init__(self,  user, items):
        self._user = user
        self._filter = items.get("filter") or {}

    @lazy
    def filter(self):
        return Filter(self._filter)

    def filter_out(self, data, filter_params=None):
        return self.filter.filter_out(data, self._user, filter_params)

    def _get_user_data(self, text_preprocessing_result=None):
        return {"message": self._user.message}

    def collect(self, text_preprocessing_result=None, filter_params=None):
        data = self._get_user_data(text_preprocessing_result)
        return self.filter_out(data, filter_params)
