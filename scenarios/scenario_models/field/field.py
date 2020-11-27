# coding: utf-8
from core.logging.logger_utils import log
from core.model.registered import Registered
import scenarios.logging.logger_constants as log_const

field_models = Registered()


def field_model_factory(description, raw_data, user, lifetime):
    _type = type(description)
    model = field_models[_type]
    instance = model(description, raw_data, user, lifetime)
    return instance


class Field:
    def __init__(self, description, items, user, lifetime):
        items = items or {}
        self.description = description
        self._value = items.get("value")
        self._available = items.get("available", self.description.available)
        self._user = user
        self._lifetime = lifetime

    def check_can_be_filled(self, text_preprocessing_result, user):
        return (
                self.description.requirement.check(text_preprocessing_result, user) and
                self.description.filler.run(user, text_preprocessing_result) is not None
        )

    def fill(self, origin_value):
        filled = False
        value = origin_value if origin_value is not None else self.default_value
        check_new_field_value = self._value != value and origin_value is not None
        can_set = value is not None and (self._value is None or check_new_field_value)

        if self.available and can_set:
            self._set_value(value)
            self.reset_available()
            filled = True
        return filled

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

    def _set_value(self, value):
        self._value = value
        message = "Field: %(description_id)s filled by value: %(field_value)s"
        params = {log_const.KEY_NAME: log_const.FILLER_RESULT_VALUE,
                  "description_id": self.description.id,
                  "field_value": str(value)}
        log(message, None, params)
        if self.description.need_save_context:
            self._user.last_fields[self.description.id].value = value
            self._user.last_fields[self.description.id].set_remove_time(self._lifetime)

    @property
    def available(self):
        return self._available

    def set_available(self):
        self._available = True

    def reset_available(self):
        self._available = self.description.available

    @property
    def valid(self):
        return self.value is not None or not self.description.required

    @property
    def can_be_updated(self):
        return self.value is not None

    @property
    def raw(self):
        result = {}
        is_value_changed = (self._value is not None and self._value != self.description.default_value)
        if is_value_changed:
            result["value"] = self._value
        if self._available != self.description.available:
            result["available"] = self._available
        return result
