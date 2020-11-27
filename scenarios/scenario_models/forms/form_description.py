# coding: utf-8
from lazy import lazy

from core.model.factory import ordered_dict_factory, build_factory
from core.model.registered import Registered
from scenarios.scenario_models.field.field_descriptions.field_description import FieldDescription

form_descriptions = Registered()

form_description_factory = build_factory(form_descriptions)


class BaseFormDescription:
    DEFAULT_FORM_LIFETIME = 1 * 24 * 60 * 60

    def __init__(self, items, id):
        self.id = id
        self.valid = items.get("valid", False)
        self.lifetime = items.get("lifetime", self.DEFAULT_FORM_LIFETIME)
        self.version = items.get("version", -1)
        self.form_description = items.get("form_description", "")


class FormDescription(BaseFormDescription):
    def __init__(self, items, id):
        super(FormDescription, self).__init__(items, id)
        self._fields = items["fields"]

    @lazy
    @ordered_dict_factory(FieldDescription)
    def fields(self):
        return self._fields


class CompositeFormDescription(BaseFormDescription):
    def __init__(self, items, id):
        super(CompositeFormDescription, self).__init__(items, id)
        self._forms = items["forms"]

    @lazy
    @ordered_dict_factory(BaseFormDescription)
    def forms(self):
        return self._forms
