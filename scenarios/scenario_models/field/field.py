# coding: utf-8
from core.logging.logger_utils import log
from core.model.registered import Registered
from core.utils.masking_message import masking
import copy

import scenarios.logging.logger_constants as log_const

field_models = Registered()


def field_model_factory(description, raw_data, user, lifetime):
    _type = type(description)
    model = field_models[_type]
    instance = model(description, raw_data, user, lifetime)
    return instance


class BasicField:

    def __init__(self, description, items, user, lifetime):
        items = items or {}
        self.description = description
        self._value = items.get("value")
        self._available = items.get("available", self.description.available)
        self._user = user
        self._lifetime = lifetime
        self._masking_fields = user.settings["template_settings"].get("masking_fields") if user is not None else []

    @property
    def value(self):
        return self._value

    @property
    def available(self):
        return self._available

    @property
    def can_be_updated(self):
        return self.value is not None

    def check_can_be_filled(self, text_preprocessing_result, user):
        return (
                self.description.requirement.check(text_preprocessing_result, user) and
                self.description.filler.run(user, text_preprocessing_result) is not None
        )

    @property
    def valid(self):
        return self.value is not None or not self.description.required

    def is_fill_need(self, value, origin_value):
        return value is not None

    def fill(self, origin_value):
        filled = False
        value = origin_value if origin_value is not None else self.description.default_value
        if self.is_fill_need(value, origin_value):
            self._set_value(value)
            self.reset_available()
            filled = True
        return filled

    def _set_value(self, value):
        self._value = value
        dict_value = {self.description.name: copy.deepcopy(value)}
        masking(dict_value, self._masking_fields)
        message = "%(class_name)s: %(description_id)s filled by value: %(field_value)s"
        params = {log_const.KEY_NAME: log_const.FILLER_RESULT_VALUE,
                  "class_name": self.__class__.__name__,
                  "description_id": self.description.id,
                  "field_value": str(dict_value[self.description.name])}
        log(message, None, params)

    def set_available(self):
        self._available = True

    def reset_available(self):
        self._available = self.description.available

    @property
    def raw(self):
        result = {}
        is_value_changed = (self._value is not None and self._value != self.description.default_value)
        if is_value_changed:
            result["value"] = self._value
        if self._available != self.description.available:
            result["available"] = self._available
        return result


class QuestionField(BasicField):
    def __init__(self, description, items, user, lifetime):
        items = items or {}
        super(QuestionField, self).__init__(description, items, user, lifetime)
        self.ask_again_counter = items.get("ask_again_counter", 0)

    @property
    def value(self):
        return self._value if self._value is not None else self.default_value

    @property
    def default_value(self):
        if self.description.need_load_context:
            prev_value = self._user.last_fields[self.description.id].value
            if prev_value is not None:
                return prev_value
        return self.description.default_value

    def is_fill_need(self, value, origin_value):
        check_new_field_value = self._value != value and origin_value is not None
        can_set = value is not None and (self._value is None or check_new_field_value)
        return self.available and can_set

    def _set_value(self, value):
        super()._set_value(value)
        if self.description.need_save_context:
            self._user.last_fields[self.description.id].value = value
            self._user.last_fields[self.description.id].set_remove_time(self._lifetime)

    @property
    def raw(self):
        result = super().raw
        if self.ask_again_counter != 0:
            result["ask_again_counter"] = self.ask_again_counter
        return result


class IntegrationField(BasicField):
    def __init__(self, description, items, user, lifetime):
        items = items or {}
        super(IntegrationField, self).__init__(description, items, user, lifetime)

    # TODO сделать required requirement
    # def valid(self, text_preprocessing_result, user, params):
    #     return self.value is not None or not self.description.required.check(text_preprocessing_result, user, params)
