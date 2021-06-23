from core.descriptions.descriptions_items import DescriptionsItems


class SmartUpdatableDescriptionsItems(DescriptionsItems):

    def update_data(self, items):
        for item_id in items.keys():
            existed_item = self._items.get(item_id)
            if existed_item:
                if existed_item.version != items[item_id].get("version", -1) or \
                        items[item_id].get("force_update"):
                    del self._items[item_id]
        redundant = set(self._items.keys()) - set(items.keys())
        for key in redundant:
            del self._items[key]
        self._raw_items = items
