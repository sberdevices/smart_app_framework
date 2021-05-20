# coding: utf-8

from core.basic_models.actions.basic_actions import Action
from core.model.factory import factory, list_factory
from scenarios.scenario_models.field_requirements.field_requirements import FieldRequirement


class FieldValidator:
    def __init__(self, items):
        self._requirement = items.get("requirement")
        self._actions = items.get("actions")

        self.requirement = self.build_requirement()
        self.actions = self.build_actions()

    @factory(FieldRequirement)
    def build_requirement(self):
        return self._requirement

    @list_factory(Action)
    def build_actions(self):
        return self._actions
