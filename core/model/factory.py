# coding: utf-8
import functools
from collections import OrderedDict

from core.model.registered import registered_factories


def build_factory(registry_models):
    def _inner(items, *args, **kwargs):
        type = items.get("type")
        model = registry_models[type]
        try:
            return model(items, *args, **kwargs)
        except:
            raise

    return _inner


def factory(type, **params):
    def _inner(func):
        @functools.wraps(func)
        def _wrap(self, *args, **kwargs):
            result = func(self, *args, **kwargs)
            result = result or {}
            cls = registered_factories[type]
            if not isinstance(result, dict):
                result = cls(result)
            else:
                result = cls(result or {}, **params)
            return result

        return _wrap

    return _inner


def list_factory(type, **params):
    def _inner(func):
        @functools.wraps(func)
        def _wrap(*args, **kwargs):
            cls = registered_factories[type]
            res = []
            for items in func(*args, **kwargs) or []:
                if not isinstance(items, dict):
                    res.append(cls(items))
                else:
                    res.append(cls(items or {}, **params))
            return res

        return _wrap

    return _inner


def dict_factory(type, has_id=True):
    def _inner(func):
        @functools.wraps(func)
        def _wrap(*args, **kwargs):
            cls = registered_factories[type]
            items_iterator = func(*args, **kwargs).items()
            if has_id:
                return {id: cls(id=id, items=items) for id, items in items_iterator or {}}
            else:
                return {id: cls(items) for id, items in items_iterator or {}}

        return _wrap

    return _inner


def ordered_dict_factory(type, has_id=True):
    def _inner(func):
        @functools.wraps(func)
        def _wrap(*args, **kwargs):
            cls = registered_factories[type]
            items_iterator = func(*args, **kwargs).items()
            result = OrderedDict({})
            for id, items in items_iterator:
                result[id] = cls(id=id, items=items) if has_id else \
                    cls(items)
            return result

        return _wrap

    return _inner
