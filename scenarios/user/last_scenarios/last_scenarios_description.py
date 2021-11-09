# coding: utf-8
import asyncio

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
        loop = asyncio.get_event_loop()
        return user.message.channel in self._channels and \
            loop.run_until_complete(self.requirement.check(text_preprocessing_result, user)) if self._channels else \
            loop.run_until_complete(self.requirement.check(text_preprocessing_result, user))
