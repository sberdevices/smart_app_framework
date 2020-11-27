# coding: utf-8
from collections import deque

from core.model.lazy_items import LazyItems


class LimitedQueuedHashableObjects:
    def __init__(self, items, description, user=None):
        self.description = description
        self.queue = deque(items or [], maxlen=description.max_len)

    def get_list(self):
        return list(self.queue)

    def add(self, id):
        self.queue.append(id)

    def clear(self):
        self.queue.clear()

    def check(self, id):
        duplicated = id in self.queue
        if not duplicated:
            self.add(id)
        return duplicated

    @property
    def raw(self):
        return self.get_list()


class LimitedQueuedHashableObjectsItems(LazyItems):
    def __init__(self, items, descriptions, user):
        super(LimitedQueuedHashableObjectsItems, self).__init__(items, descriptions, user, LimitedQueuedHashableObjects)
