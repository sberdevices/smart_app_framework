# coding: utf-8
import asyncio
from typing import Dict, List, Optional, Any, Set

from core.basic_models.operators.operators import Operator
from core.model.factory import factory, build_factory, list_factory
from core.model.registered import Registered

field_requirements = Registered()

field_requirement_factory = build_factory(field_requirements)


class FieldRequirement:
    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        pass

    async def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return True


class CompositeFieldRequirement(FieldRequirement):
    requirements: List[FieldRequirement]

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(CompositeFieldRequirement, self).__init__(items)
        self._requirements: List[Dict[str, Any]] = items["requirements"]
        self.requirements = self.build_requirements()

    @list_factory(FieldRequirement)
    def build_requirements(self):
        return self._requirements


class AndFieldRequirement(CompositeFieldRequirement):
    async def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return all(await requirement.check(field_value=field_value, params=params) for requirement in self.requirements)


class GatherAndFieldRequirement(CompositeFieldRequirement):
    async def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        check_results = await asyncio.gather(requirement.check(field_value=field_value, params=params)
                                             for requirement in self.requirements)
        return all(check_results)


class OrFieldRequirement(CompositeFieldRequirement):
    async def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return any(await requirement.check(field_value=field_value, params=params) for requirement in self.requirements)


class GatherOrFieldRequirement(CompositeFieldRequirement):
    async def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        check_results = await asyncio.gather(requirement.check(field_value=field_value, params=params)
                                             for requirement in self.requirements)
        return any(check_results)


class NotFieldRequirement(FieldRequirement):
    requirement: FieldRequirement

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(NotFieldRequirement, self).__init__(items)
        self._requirement: Dict[str, Any] = items["requirement"]
        self.requirement = self.build_requirement()

    @factory(FieldRequirement)
    def build_requirement(self):
        return self._requirement

    async def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return not await self.requirement.check(field_value=field_value, params=params)


class ComparisonFieldRequirement(FieldRequirement):
    operator: Operator

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(ComparisonFieldRequirement, self).__init__(items)
        self._operator: Dict[str, Any] = items["operator"]
        self.operator = self.build_operator()

    @factory(Operator)
    def build_operator(self):
        return self._operator

    async def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return self.operator.compare(field_value)


class IsIntFieldRequirement(FieldRequirement):
    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(IsIntFieldRequirement, self).__init__(items)

    async def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
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

    async def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return field_value in self.symbols


class TokenPartInSet(FieldRequirement):
    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(TokenPartInSet, self).__init__(items)
        self.part = items['part']
        self.values = items['values']

    async def check(self, field_value: dict, params: Dict[str, Any] = None) -> bool:
        return field_value[self.part] in self.values


class TextLengthFieldRequirement(FieldRequirement):
    min_field_length: int
    max_field_length: int

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(TextLengthFieldRequirement, self).__init__(items)
        self.min_field_length = items["min_field_length"]
        self.max_field_length = items["max_field_length"]

    async def check(self, field_value: str, params: Dict[str, Any] = None) -> bool:
        return self.min_field_length <= len(field_value) <= self.max_field_length
