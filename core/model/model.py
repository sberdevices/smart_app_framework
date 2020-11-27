# coding: utf-8


class Model:
    @property
    def fields(self):
        return []

    def __init__(self, values, user):
        values = values or {}

        for field in self.fields:
            value = values.get(field.name)
            description = field.description
            args = field.args
            if description is not None:
                obj = field.model(value, description, user, *args)
            else:
                obj = field.model(value, user, *args)
            setattr(self, field.name, obj)

    def get_field(self, name):
        return getattr(self, name)

    @property
    def raw(self):
        result = {}
        for field in self.fields:
            value = getattr(self, field.name)
            raw = value.raw
            if raw is not None:
                result[field.name] = raw
        return result
