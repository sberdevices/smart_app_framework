import functools
import typing
import tabulate

DoesNotExpected = object()


class Diff:
    def __init__(self):
        self.missed: typing.Dict[str, typing.Any] = {}  # key : expected
        self.different: typing.Dict[str, typing.Tuple[typing.Any, typing.Any]] = {}  # key: expected,actual
        self.does_not_expected: typing.Dict[str, typing.Any] = {}  # key: actual

    def update(self, other):
        self.missed.update(other.missed)
        self.different.update(other.different)
        self.does_not_expected.update(other.does_not_expected)

    def __bool__(self):
        return bool(self.missed or self.different)

    def __str__(self):
        missed = ""
        does_not_expected = ""
        different = ""
        if self.missed:
            missed = "Missed:\n" + tabulate.tabulate(self.missed.items(), headers=["Key", "Expected"])
        if self.does_not_expected:
            does_not_expected = "Does Not Expected:\n"
            does_not_expected += tabulate.tabulate(self.does_not_expected.items(), headers=["Key", "Actual"])
        if self.different:
            different = "Different:\n"
            different += tabulate.tabulate(
                [(k, d[0], d[1]) for k, d in self.different.items()], headers=["Key", "Expected", "Actual"]
            )

        return "\n".join((missed, does_not_expected, different))


@functools.singledispatch
def partial_diff(expected: typing.Any, actual: typing.Any, path="") -> Diff:
    diff = Diff()
    if expected != actual:
        diff.different[path] = expected, actual
    return diff


@partial_diff.register(list)
def partial_diff_list(expected: list, actual: list, path="") -> Diff:
    diff = Diff()
    does_not_expected = [DoesNotExpected for _ in range(len(expected), len(actual))]

    for index, exp_element in enumerate(expected + does_not_expected):
        sub_path = f"{path}[{index + 1}]" if path else f"[{index + 1}]"
        try:
            if exp_element == DoesNotExpected:
                diff.does_not_expected[sub_path] = actual[index]
            else:
                diff.update(partial_diff(exp_element, actual[index], sub_path))
        except IndexError:
            diff.missed[sub_path] = exp_element

    return diff


@partial_diff.register(dict)
def partial_diff_dict(expected, actual, path="") -> Diff:
    diff = Diff()
    for key, value in expected.items():
        sub_path = f"{path}.{key}" if path else str(key)
        if key not in actual:
            diff.missed[sub_path] = value
            continue

        diff.update(partial_diff(value, actual[key], sub_path))
    return diff
