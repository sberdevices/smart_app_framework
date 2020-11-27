from typing import Union
from lazy import lazy

from core.model.factory import factory
from scenarios.scenario_models.history import EventFormatter


class HistoryDescription:
    enabled: bool
    event_expiration_delay: Union[int, float]

    EVENT_EXPIRATION_DELAY = 60

    def __init__(self, items, id=None):
        self.id = id
        self.enabled = items.get("enabled", False)
        self.event_expiration_delay = items.get("event_expiration_delay", self.EVENT_EXPIRATION_DELAY)
        self._formatter = items.get("formatter")

    @lazy
    @factory(EventFormatter)
    def formatter(self) -> EventFormatter:
        return self._formatter
