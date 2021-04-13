# coding: utf-8
from lazy import lazy

from core.basic_models.requirement.basic_requirements import Requirement
from core.model.factory import factory

from scenarios.scenario_models.field.field_descriptions.basic_field_description import BasicFieldDescription


class IntegrationFieldDescription(BasicFieldDescription):

    def __init__(self, items, id):
        super(IntegrationFieldDescription, self).__init__(items, id)
        self._retry_count = items.get("retry_count", 0)
