import time
import json


class ItemExpired(Exception):
    pass


class Cache:
    def __init__(self, lifetime: float = 0):
        self.lifetime = lifetime
        self.storage = dict()

    def __getitem__(self, item):
        create_time, value = self.storage[item]
        if create_time + self.lifetime <= time.time():
            raise ItemExpired
        return value

    def __setitem__(self, key, value):
        self.storage[key] = time.time(), value

    def load(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        pass

    def invalidate(self):
        for key in list(self.storage):
            try:
                self[key]
            except ItemExpired:
                del self.storage[key]

    def clear(self):
        self.storage.clear()


class JSONCache(Cache):  # Pathetic Non OOP Design, Sorry
    def load(self, path):
        with open(path) as file:
            self.storage = json.load(file)

    def save(self, path, update=False):
        if update:
            tmp = JSONCache(lifetime=float("+inf"))
            tmp.load(path)
            tmp.storage.update(self.storage)
            self.storage = tmp.storage
        self.invalidate()
        with open(path, "w+", encoding='utf-8') as file:
            json.dump(self.storage, file, ensure_ascii=False)
