import time

from core.model.registered import Registered
from scenarios.scenario_models.field.field import field_model_factory
from scenarios.scenario_models.field.fields import Fields

form_models = Registered()


def form_model_factory(value, description, user):
    _type = type(description)
    model = form_models[_type]
    return model(value, description, user)


class BaseForm:
    def __init__(self, items, description, user):
        items = items or {}
        self.description = description
        self._valid = self.description.valid
        self._user = user
        self.remove_time = items.get("remove_time")

    def touch(self):
        lifetime = self.description.lifetime
        if lifetime:
            self.remove_time = int(time.time()) + lifetime

    def check_expired(self):
        return time.time() >= self.remove_time if self.remove_time else False

    @property
    def raw(self):
        raise NotImplementedError

    def get_fields_values(self):
        raise NotImplementedError


class Form(BaseForm):
    def __init__(self, items, description, user):
        super(Form, self).__init__(items, description, user)
        items = items or {}
        self.fields = Fields(items.get("fields"), description.fields, user, field_model_factory, description.lifetime)

    def is_valid(self):
        if not self._valid:
            self._valid = all(self.fields[description].valid for description in self.fields)
        return self._valid

    def refresh(self):
        self.touch()
        for description in self.fields:
            if description.need_save_context:
                self._user.last_fields[description.id].set_remove_time(self.description.lifetime)

    def get_fields_values(self):
        return {self.description.id: self.fields.values}

    @property
    def raw(self):
        raw = {}
        if self.fields.raw:
            raw["fields"] = self.fields.raw
        if self.remove_time:
            raw["remove_time"] = self.remove_time
        return raw
