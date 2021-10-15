# coding: utf-8
from lazy import lazy

from core.basic_models.actions.basic_actions import Action
from core.basic_models.requirement.basic_requirements import Requirement
from core.model.factory import factory, list_factory, build_factory
from core.model.registered import Registered
from scenarios.scenario_models.field.field_filler_description import FieldFillerDescription
from scenarios.scenario_models.field_validator.field_validator import FieldValidator

field_descriptions = Registered()

field_description_factory = build_factory(field_descriptions)


class BasicFieldDescription:
    DEFAULT_AVAILABLE_VALUE = True

    def __init__(self, items, id):
        self.id = id
        self.name = id
        self.type = items.get("type")
        self._required = items.get("required", False)
        self._filler = items.get("filler")
        self.default_value = items.get("default_value")
        self.available = items.get("available", self.DEFAULT_AVAILABLE_VALUE)
        self._requests = items.get("requests", [])
        self._on_filled_actions = items.get("on_filled_actions", [])
        self._requirement = items.get("requirement")
        self._field_validator = items.get("field_validator")
        self.need_save_context = items.get("need_save_context", False)
        self.need_load_context = items.get("need_load_context", False)
        self.fill_other = items.get("fill_other", True)
        self._ask_again_requests = items.get("ask_again_questions", [])

    @lazy
    @list_factory(Action)
    def requests(self):
        return self._requests

    @lazy
    @list_factory(Action)
    def on_filled_actions(self):
        return self._on_filled_actions

    @property
    def has_requests(self):
        return True if self._requests else False

    @property
    def required(self):
        return self._required

    @lazy
    @factory(Requirement)
    def requirement(self):
        return self._requirement

    @lazy
    @factory(FieldFillerDescription)
    def filler(self):
        return self._filler

    @lazy
    @factory(FieldValidator)
    def field_validator(self):
        return self._field_validator
