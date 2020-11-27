# coding: utf-8
from lazy import lazy

from core.basic_models.requirement.basic_requirements import Requirement
from core.model.factory import factory


class LastScenariosDescription:
    def __init__(self, items, id):
        self.id = id
        self._channels = items.get("channels")
        self._requirement = items.get("requirement")
        self.count = items.get("count", 1)

    @lazy
    @factory(Requirement)
    def requirement(self):
        return self._requirement

    def check(self, text_preprocessing_result, user):
        return user.message.channel in self._channels and self.requirement.check(text_preprocessing_result, user) if \
            self._channels else self.requirement.check(text_preprocessing_result, user)
