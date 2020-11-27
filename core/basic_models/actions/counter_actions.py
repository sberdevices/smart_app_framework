# coding: utf-8
from typing import Union, Dict, Any, Optional

from core.basic_models.actions.basic_actions import Action
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.model.base_user import BaseUser


class CounterIncrementAction(Action):
    version: Optional[int]
    key: str
    value: int

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(CounterIncrementAction, self).__init__(items, id)
        items = items or {}
        self.key = items["key"]
        self.value = items.get("value", 1)
        self.lifetime = items.get("lifetime")

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        user.counters[self.key].inc(self.value, self.lifetime)


class CounterDecrementAction(CounterIncrementAction):
    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        user.counters[self.key].dec(-self.value, self.lifetime)


class CounterClearAction(CounterIncrementAction):
    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        user.counters.clear(self.key)


class CounterSetAction(CounterIncrementAction):
    version: Optional[int]
    key: str
    value: Optional[int]
    reset_time: bool
    time_shift: Optional[int]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(CounterSetAction, self).__init__(items, id)
        self.value = items.get("value")
        self.reset_time = items.get("reset_time", False)
        self.time_shift = items.get("time_shift", 0)

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        user.counters[self.key].set(self.value, self.reset_time, self.time_shift)


class CounterCopyAction(Action):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(CounterCopyAction, self).__init__(items, id)
        self.src = items["source"]
        self.dst = items["destination"]
        self.reset_time = items.get("reset_time", False)
        self.time_shift = items.get("time_shift", 0)

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        value = user.counters[self.src].value
        user.counters[self.dst].set(value, self.reset_time, self.time_shift)
