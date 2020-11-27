# coding: utf-8
from lazy import lazy

from core.basic_models.actions.basic_actions import Action
from core.basic_models.requirement.basic_requirements import Requirement
from core.model.factory import factory, list_factory


class TreeScenarioNode:
    def __init__(self, items, id):
        items = items or {}
        self.id = id
        self.form_key = items["form_key"]
        self._requirement = items.get("requirement")
        self._actions = items.get("actions")
        self.available_nodes = items.get("available_nodes")

    @lazy
    @factory(Requirement)
    def requirement(self):
        return self._requirement

    @lazy
    @list_factory(Action)
    def actions(self):
        return self._actions
