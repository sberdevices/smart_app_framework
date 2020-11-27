# coding: utf-8


class LazyItems:
    def __init__(self, items, descriptions, user, factory):
        self._descriptions = descriptions
        self._factory = factory
        self._raw_items = items or {}
        self._items = dict()
        self._user = user
        self._clear_removed_items()

    def _clear_removed_items(self):
        keys_for_delete = []
        for key in self._raw_items:
            if not key in self._descriptions:
                keys_for_delete.append(key)
        for key in keys_for_delete:
            self._raw_items.pop(key)

    def __getitem__(self, description):
        if hasattr(description, "id"):
            id = description.id
        else:
            id = description
            description = self._descriptions[id]
        existed_item = self._items.get(description)
        if existed_item is None:
            raw_data = self._raw_items.get(id)
            existed_item = self._build_factory(description, raw_data)
            self._items[description] = existed_item
        return existed_item

    def _build_factory(self, description, raw_data):
        return self._factory(raw_data, description, self._user)

    def __setitem__(self, description, value):
        self._items[description] = value

    def __iter__(self):
        return iter(self._descriptions[key] for key in self._descriptions)

    def remove_item(self, descr_id):
        description = self._descriptions[descr_id]
        if description in self._items:
            self._items.pop(description)
        if descr_id in self._raw_items:
            self._raw_items.pop(descr_id)

    @property
    def descriptions(self):
        return self._descriptions

    @property
    def raw(self):
        for i in self._items:
            item = self._items[i]
            value = getattr(item, "raw", item)
            if value is not None:
                self._raw_items[i.id] = value
            else:
                if i.id in self._raw_items:
                    self._raw_items.pop(i.id)
        return self._raw_items
