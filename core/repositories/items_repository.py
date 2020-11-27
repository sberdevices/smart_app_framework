# coding: utf-8

from core.repositories.base_repository import BaseRepository


class ItemsRepository(BaseRepository):
    def __init__(self, *args, **kwargs):
        super(ItemsRepository, self).__init__(*args, **kwargs)
        self.data = dict()

    @BaseRepository.data.setter
    def data(self, value):
        if value is None:
            self._data = dict()
        else:
            self._data = value

    def load(self):
        super(ItemsRepository, self).load()

    def __iter__(self):
        return iter(self.data)

    def __len__(self):
        return len(self.data)
