# coding: utf-8
from lazy import lazy

from core.basic_models.actions.basic_actions import Action
from core.model.factory import list_factory

from scenarios.scenario_models.field.field_descriptions.basic_field_description import BasicFieldDescription


class QuestionFieldDescription(BasicFieldDescription):
    DEFAULT_AVAILABLE_VALUE = True

    def __init__(self, items, id):
        super(QuestionFieldDescription, self).__init__(items, id)
        self._requests = items.get("questions", [])
        self._on_filled_actions = items.get("on_filled_actions", [])
        self._ask_again_requests = items.get("ask_again_questions", [])

    @lazy
    @list_factory(Action)
    def ask_again_requests(self):
        return self._ask_again_requests
