import os
from core.repositories.base_repository import BaseRepository


class ShardRepository(BaseRepository):

    def __init__(self, path, loader, source=None, *args, **kwargs):
        super(ShardRepository, self).__init__(source=source, *args, **kwargs)
        self.path = path
        self.loader = loader

    @staticmethod
    def join_path(path, file_name):
        path = os.path.join(path, file_name)
        path = os.path.normpath(path)
        return path

    @staticmethod
    def _get_data_type(data):
        t = None
        for k, v in data.items():
            if not t:
                if isinstance(v, dict):
                    t = dict
                elif isinstance(v, list):
                    t = list
            if t and not isinstance(v, t):
                raise TypeError(
                    f"There are more than one data type in folder repository: values {v} incompatible with"
                    f" data type {t}")
        return t

    def load(self):
        super(ShardRepository, self).load()

    def fill(self, data):
        res = None
        t = self._get_data_type(data)
        if t == dict:
            res = {}
            for k, v in data.items():
                res.update(v)
        elif t == list:
            res = []
            for k, v in data.items():
                res.extend(v)
        self.data = res

    def fill_on_top(self, data):
        t = self._get_data_type(data)
        for k, v in data.items():
            if t == dict:
                self.data.update(v)
            elif t == list:
                self.data.extend(v)

    def save(self, save_parameters):
        raise NotImplementedError
