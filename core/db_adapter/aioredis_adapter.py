import aioredis
import typing

from core.db_adapter.db_adapter import DBAdapter
from core.db_adapter import error
from core.monitoring.monitoring import monitoring


class AIORedisAdapter(DBAdapter):
    IS_ASYNC = True

    def __init__(self, config=None):
        super().__init__(config)
        self._redis: typing.Optional[aioredis.Redis] = None

        try:
            del self.config["type"]
        except KeyError:
            pass

    @monitoring.got_histogram("save_time")
    async def save(self, id, data):
        return await self._run(self._save, id, data)

    @monitoring.got_histogram("save_time")
    async def replace_if_equals(self, id, sample, data):
        return await self._run(self._replace_if_equals, id, sample, data)

    @monitoring.got_histogram("get_time")
    async def get(self, id):
        return await self._run(self._get, id)

    async def path_exists(self, path):
        return await self._run(self._path_exists, path)

    async def connect(self):
        self._redis = await aioredis.create_redis_pool(**self.config)

    def _open(self, filename, *args, **kwargs):
        pass

    async def _save(self, id, data):
        return await self._redis.set(id, data)

    async def _replace_if_equals(self, id, sample, data):
        if data == sample:
            return await self._redis.touch(id)
        return False

    async def _get(self, id):
        data = await self._redis.get(id)
        return data.decode() if data else None

    def _list_dir(self, path):
        raise error.NotSupportedOperation

    def _glob(self, path, pattern):
        raise error.NotSupportedOperation

    async def _path_exists(self, path):
        return await self._redis.exists(path)

    def _on_prepare(self):
        pass
