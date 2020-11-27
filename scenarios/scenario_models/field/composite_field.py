# coding: utf-8
from scenarios.scenario_models.field.field import field_model_factory
from scenarios.scenario_models.field.fields import Fields


class CompositeField:
    def __init__(self, description, items, user, lifetime):
        self.description = description
        self._user = user
        self._lifetime = lifetime
        self.fields = Fields(items.get("fields"), description.fields, user, field_model_factory, lifetime)

    def fill(self, value):
        any_filled = False
        if value:
            for field_descr in self.fields:
                filled = self.fields[field_descr].fill(value.get(field_descr.id))
                any_filled = any_filled or filled
        # when any inner field is filled at this run and all fields are valid for the time
        return any_filled and self.valid

    @property
    def value(self):
        value = {}
        for field_descr in self.fields:
            field = self.fields[field_descr]
            if field.value:
                value[field_descr.id] = field.value
        return value

    @property
    def available(self):
        return all([self.fields[field_descr].available for field_descr in self.fields])

    def set_available(self):
        for field_descr in self.fields:
            self.fields[field_descr].set_available()

    @property
    def valid(self):
        return all(self.fields[field_descr].valid for field_descr in self.fields)

    @property
    def raw(self):
        fields = {}
        for field_descr in self.fields:
            field = self.fields[field_descr]
            if field.raw:
                fields[field_descr.id] = field.raw
        raw = {}
        if fields:
            raw["fields"] = fields
        return raw
