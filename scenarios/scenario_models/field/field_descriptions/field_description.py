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


class FieldDescription:
    DEFAULT_AVAILABLE_VALUE = True

    def __init__(self, items, id):
        self.id = id
        self.name = id
        self.required = items.get("required", False)
        self._filler = items.get("filler")
        self.default_value = items.get("default_value")
        self.need_save_context = items.get("need_save_context", False)
        self.need_load_context = items.get("need_load_context", False)
        self.available = items.get("available", self.DEFAULT_AVAILABLE_VALUE)
        self._questions = items.get("questions", [])
        self._on_filled_actions = items.get("on_filled_actions", [])
        self.is_comment = items.get("is_comment", False)
        self.fill_other = items.get("fill_other", True)
        self._requirement = items.get("requirement")
        self._field_validator = items.get("field_validator")
        self._ask_again_question = items.get("ask_again_question")
        self.has_again_question = bool(self._ask_again_question)

    @lazy
    @list_factory(Action)
    def questions(self):
        return self._questions

    @lazy
    @factory(Action)
    def ask_again_question(self):
        return self._ask_again_question

    @lazy
    @list_factory(Action)
    def on_filled_actions(self):
        return self._on_filled_actions

    @property
    def has_questions(self):
        return True if self._questions else False

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
