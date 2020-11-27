from typing import Dict, Any, Optional

from core.model.base_user import BaseUser

from core.text_preprocessing.base import BaseTextPreprocessingResult

from core.basic_models.operators.operators import Operator
from core.basic_models.requirement.basic_requirements import ComparisonRequirement
from time import time


class CounterValueRequirement(ComparisonRequirement):
    operator: Operator
    key: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(CounterValueRequirement, self).__init__(items, id)
        items = items or {}
        self.key = items["key"]

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        counter = user.counters[self.key]
        return self.operator.compare(counter)


class CounterUpdateTimeRequirement(ComparisonRequirement):
    operator: Operator
    key: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(CounterUpdateTimeRequirement, self).__init__(items, id)
        items = items or {}
        self.key = items["key"]
        self.fallback_value = items.get("fallback_value") or False

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        _time = user.counters[self.key].update_time
        return self.operator.compare(time() - _time) if _time else self.fallback_value
