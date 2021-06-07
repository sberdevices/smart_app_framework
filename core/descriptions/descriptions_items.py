# coding=utf-8


class DescriptionsItems:
    def __init__(self, factory, items, ordered=False):
        items = items or {}
        self._factory = factory
        self._raw_items = None
        self._items = None
        self._init(items)

    def __contains__(self, key):
        return key in self._raw_items

    def _init(self, raw_items):
        self._raw_items = raw_items
        self._items = dict()
        for id in self._raw_items.keys():
            self._get_or_create_item(id)

    def __getitem__(self, id):
        return self._get_or_create_item(id)

    def _get_or_create_item(self, id):
        existed_item = self._items.get(id)
        if existed_item is None:
            existed_item = self._factory(id=id, items=self._raw_items[id])
            self._items[id] = existed_item
        return existed_item

    # should implement python dictionary interface
    def get(self, key):
        if key in self:
            return self.__getitem__(key)

    def __len__(self):
        return len(self._raw_items)

    def __iter__(self):
        return iter(self._raw_items)

    def get_keys(self):
        return self._raw_items.keys()

    def keys(self):
        return self._raw_items.keys()

    def update_data(self, items):
        self._init(items)

    def update_item(self, key, item):
        if key in self._items:
            del self._items[key]
        self._raw_items[key] = item
        self._get_or_create_item(key)

    def remove_item(self, key):
        if key in self._items:
            del self._items[key]
        if key in self._raw_items:
            del self._raw_items[key]
