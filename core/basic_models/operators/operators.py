# coding: utf-8
from typing import Union, Any, Dict, List, Optional

from core.basic_models.operators.comparators import MoreComparator, LessComparator, MoreOrEqualComparator, \
    LessOrEqualComparator, EqualComparator, NotEqualComparator, InComparator, Comparator
from core.model.factory import build_factory, list_factory
from core.model.registered import Registered

operators = Registered()

operator_factory = build_factory(operators)


class Operator:

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        pass

    def compare(self, value: Any) -> bool:
        raise NotImplementedError


class CompositeOperator(Operator):
    operators: List[Operator]

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(CompositeOperator, self).__init__(items)
        self._operators: Dict[str, Any] = items["operators"]
        self.operators = self.build_operators()

    @list_factory(Operator)
    def build_operators(self):
        return self._operators

    def compare(self, value: Any) -> bool:
        return all(operator.compare(value) for operator in self.operators)


class AnyOperator(CompositeOperator):
    def compare(self, value: Any) -> bool:
        return any(operator.compare(value) for operator in self.operators)


class AmountOperator(Operator):
    amount: Union[int, str, List]
    comparator: Comparator

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(AmountOperator, self).__init__(items)
        self.amount = items["amount"]
        self.comparator: Optional[Comparator] = None

    def compare(self, value: Union[int, str]):
        return self.comparator.compare(value, self.amount)


class InOperator(AmountOperator):
    amount: Union[int, str, List]
    comparator: InComparator

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(InOperator, self).__init__(items)
        self.comparator = InComparator({})


class MoreOperator(AmountOperator):
    amount: Union[int, str, List]
    comparator: MoreComparator

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(MoreOperator, self).__init__(items)
        self.comparator = MoreComparator({})


class LessOperator(AmountOperator):
    amount: Union[int, str, List]
    comparator: LessComparator

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(LessOperator, self).__init__(items)
        self.comparator = LessComparator({})


class MoreOrEqualOperator(AmountOperator):
    amount: Union[int, str, List]
    comparator: MoreOrEqualComparator

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(MoreOrEqualOperator, self).__init__(items)
        self.comparator = MoreOrEqualComparator({})


class LessOrEqualOperator(AmountOperator):
    amount: Union[int, str, List]
    comparator: LessOrEqualComparator

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(LessOrEqualOperator, self).__init__(items)
        self.comparator = LessOrEqualComparator({})


class EqualOperator(AmountOperator):
    amount: Union[int, str, List]
    comparator: EqualComparator

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(EqualOperator, self).__init__(items)
        self.comparator = EqualComparator({})


class NotEqualOperator(AmountOperator):
    amount: Union[int, str, List]
    comparator: NotEqualComparator

    def __init__(self, items: Optional[Dict[str, Any]]) -> None:
        super(NotEqualOperator, self).__init__(items)
        self.comparator = NotEqualComparator({})


class Exists(Operator):
    def compare(self, value: Any) -> bool:
        return True if value is not None else False


class EndsWithOperator(AmountOperator):
    """
    Оператор проверяет, оканчивается ли значение на amount
    """

    def compare(self, value: Union[int, str]) -> bool:
        return str(value).endswith(str(self.amount)) if value else False


class StartsWithOperator(AmountOperator):
    """
    Оператор проверяет, начинается ли значение с amount
    """

    def compare(self, value: Union[int, str]) -> bool:
        return str(value).startswith(str(self.amount)) if value else False
