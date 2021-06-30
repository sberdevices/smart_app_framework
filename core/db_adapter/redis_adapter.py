import redis
import typing
from core.db_adapter.db_adapter import DBAdapter
from core.db_adapter import error


class RedisAdapter(DBAdapter):
    def __init__(self, config=None):
        super().__init__(config)
        self._redis: typing.Optional[redis.Redis] = None

        try:
            del self.config["type"]
        except KeyError:
            pass

    def connect(self):
        self._redis = redis.Redis(**self.config)

    def _open(self, filename, *args, **kwargs):
        pass

    def _save(self, id, data):
        return self._redis.set(id, data)

    def _replace_if_equals(self, id, sample, data):
        return self._redis.set(id, data)

    def _get(self, id):
        data = self._redis.get(id)
        return data.decode() if data else None

    def _list_dir(self, path):
        raise error.NotSupportedOperation

    def _glob(self, path, pattern):
        raise error.NotSupportedOperation

    def _path_exists(self, path):
        self._redis.exists(path)

    def _on_prepare(self):
        pass
