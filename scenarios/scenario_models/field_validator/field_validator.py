# coding: utf-8
from lazy import lazy

from core.model.factory import factory, list_factory
from core.basic_models.actions.basic_actions import Action
from scenarios.scenario_models.field_requirements.field_requirements import FieldRequirement


class FieldValidator:
    def __init__(self, items):
        self._requirement = items.get("requirement")
        self._actions = items.get("actions")

    @lazy
    @factory(FieldRequirement)
    def requirement(self):
        return self._requirement

    @lazy
    @list_factory(Action)
    def actions(self):
        return self._actions
