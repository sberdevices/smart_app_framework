# coding: utf-8

from core.model.factory import ordered_dict_factory, build_factory
from core.model.registered import Registered
from scenarios.scenario_models.field.field_descriptions.basic_field_description import BasicFieldDescription

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
        self.fields = self.build_fields()

    @ordered_dict_factory(BasicFieldDescription)
    def build_fields(self):
        return self._fields


class CompositeFormDescription(BaseFormDescription):
    def __init__(self, items, id):
        super(CompositeFormDescription, self).__init__(items, id)
        self._forms = items["forms"]
        self.forms = self.build_forms()

    @ordered_dict_factory(BaseFormDescription)
    def build_forms(self):
        return self._forms
