# coding: utf-8
from core.model.lazy_items import LazyItems


class Fields(LazyItems):
    def __init__(self, items, descriptions, user, factory, lifetime):
        self._lifetime = lifetime
        super(Fields, self).__init__(items, descriptions, user, factory)

    def _build_factory(self, description, raw_data):
        return self._factory(description, raw_data or {}, self._user, self._lifetime)

    @property
    def values(self):
        result = dict()
        for key in self:
            item = self[key]
            result[item.description.id] = item.value
        return result
