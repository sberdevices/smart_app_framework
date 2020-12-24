from lazy import lazy

from core.model.factory import dict_factory, factory
from scenarios.scenario_models.field.field_filler_description import FieldFillerDescription
from scenarios.scenario_models.field.field_descriptions.basic_field_description import BasicFieldDescription


class CompositeFieldDescription(BasicFieldDescription):

    def __init__(self, items, id):
        super(CompositeFieldDescription, self).__init__(items, id)
        self._fields = items["fields"]

    @lazy
    @factory(FieldFillerDescription)
    def filler(self):
        return self._filler

    @lazy
    @dict_factory(BasicFieldDescription)
    def fields(self):
        return self._fields
