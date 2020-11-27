import functools
from typing import Optional


def fallback_if_none(fallback_result_value=None, fallback_result_attr: Optional[str] = None):
    """ Parametrized function decorator that returns value if original function has returned None.
    Fallback value could be specified explicitly or specified by attribute name (for class methods).
    If fallback value cannot be resolved - an exception is thrown.

    :param fallback_result_value: Explicit fallback value to return
    :param fallback_result_attr: Name of the attribute of the object that method assigned to
    :return: decorator
    """
    def _decorator(fn):
        @functools.wraps(fn)
        def _wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            if result is not None:
                return result
            if fallback_result_value is not None:
                return fallback_result_value
            if fallback_result_attr is not None:
                fallback_result = getattr(args[0], fallback_result_attr)
                if fallback_result is not None:
                    return fallback_result
            raise ValueError(f'Function {fn.__module__}:{fn.__name__} has returned None, '
                             f'but fallback value or fallback attribute is not specified. Check decorator usage')
        return _wrapper
    return _decorator
