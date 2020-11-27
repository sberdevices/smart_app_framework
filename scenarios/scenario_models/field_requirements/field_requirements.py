# coding: utf-8
from lazy import lazy
from typing import Dict, List, Optional, Any, Set

from core.model.factory import factory, build_factory, list_factory
from core.model.registered import Registered
from core.basic_models.operators.operators import Operator


field_requirements = Registered()

field_requirement_factory = build_factory(field_requirements)


class FieldRequirement:
    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        pass

    def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return True


class CompositeFieldRequirement(FieldRequirement):
    requirements: List[FieldRequirement]

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(CompositeFieldRequirement, self).__init__(items)
        self._requirements: List[Dict[str, Any]] = items["requirements"]

    @lazy
    @list_factory(FieldRequirement)
    def requirements(self):
        return self._requirements


class AndFieldRequirement(CompositeFieldRequirement):
    def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return all(requirement.check(field_value=field_value, params=params) for requirement in self.requirements)


class OrFieldRequirement(CompositeFieldRequirement):
    def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return any(requirement.check(field_value=field_value, params=params) for requirement in self.requirements)


class NotFieldRequirement(FieldRequirement):
    requirement: FieldRequirement

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(NotFieldRequirement, self).__init__(items)
        self._requirement: Dict[str, Any] = items["requirement"]

    @lazy
    @factory(FieldRequirement)
    def requirement(self):
        return self._requirement

    def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return not self.requirement.check(field_value=field_value, params=params)


class ComparisonFieldRequirement(FieldRequirement):
    operator: Operator

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(ComparisonFieldRequirement, self).__init__(items)
        self._operator: Dict[str, Any] = items["operator"]

    @lazy
    @factory(Operator)
    def operator(self):
        return self._operator

    def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return self.operator.compare(field_value)


class IsIntFieldRequirement(FieldRequirement):
    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(IsIntFieldRequirement, self).__init__(items)

    def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        try:
            int(field_value)
            return True
        except ValueError:
            return False


class ValueInSetRequirement(FieldRequirement):
    symbols: List

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(ValueInSetRequirement, self).__init__(items)
        self.symbols: Set = set(items["symbols"])

    def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return field_value in self.symbols


class TokenPartInSet(FieldRequirement):
    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(TokenPartInSet, self).__init__(items)
        self.part = items['part']
        self.values = items['values']

    def check(self, field_value: dict, params: Dict[str, Any] = None) -> bool:
        return field_value[self.part] in self.values


class TextLengthFieldRequirement(FieldRequirement):
    min_field_length: int
    max_field_length: int

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(TextLengthFieldRequirement, self).__init__(items)
        self.min_field_length = items["min_field_length"]
        self.max_field_length = items["max_field_length"]

    def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return self.min_field_length <= len(field_value) <= self.max_field_length
