from core.descriptions.lazy_descriptions import LazyDescriptions


class LimitedQueuedHashableObjectsDescription:
    DEFAULT_MAX_LEN = 10

    def __init__(self, items, id=None):
        self.id = id
        self.items = items or {}
        self.max_len = self.items.get("max_len", self.DEFAULT_MAX_LEN)


class LimitedQueuedHashableObjectsDescriptions(LazyDescriptions):
    def __init__(self, items):
        super(LimitedQueuedHashableObjectsDescriptions, self).__init__(LimitedQueuedHashableObjectsDescription, items)
