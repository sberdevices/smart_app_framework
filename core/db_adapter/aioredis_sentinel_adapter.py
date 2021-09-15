import copy

import aioredis
import typing

from aioredis.sentinel import Sentinel
from core.db_adapter.db_adapter import DBAdapter
from core.db_adapter import error
from core.monitoring.monitoring import monitoring
from core.logging.logger_utils import log


class AIORedisSentinelAdapter(DBAdapter):
    IS_ASYNC = True

    def __init__(self, config=None):
        super().__init__(config)
        self._sentinel: typing.Optional[Sentinel] = None
        self.service_name = None
        self.socket_timeout = None

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

        config = copy.deepcopy(self.config)
        print("Here is the content of REDIS_CONFIG:", config)
        if not isinstance(config, dict):
            raise ValueError("REDIS_CONFIG should be a mapping")
        sentinels = config.pop("sentinels", None)
        self.service_name = config.pop("service_name", None)
        self.socket_timeout = config.get("socket_timeout", None)
        if not isinstance(sentinels, list):
            raise ValueError(
                "sentinels should be specified like [['sentinel.host1', 26379], ['sentinel.host2', 26379]]")
        sentinels_tuples = []
        for sent in sentinels:
            sentinels_tuples.append(tuple(sent))
        self._sentinel = Sentinel(sentinels_tuples, **config)

    def _open(self, filename, *args, **kwargs):
        pass

    async def _save(self, id, data):
        redis = await self._sentinel.master_for(self.service_name, socket_timeout=self.socket_timeout)
        await redis.set(id, data)

    async def _replace_if_equals(self, id, sample, data):
        log("no replace_if_equals method. running save instead", level="WARNING")
        await self.save(id, data)

    async def _get(self, id):
        redis = await self._sentinel.master_for(self.service_name, socket_timeout=self.socket_timeout)
        data = await redis.get(id)
        return data

    def _list_dir(self, path):
        raise error.NotSupportedOperation

    def _glob(self, path, pattern):
        raise error.NotSupportedOperation

    async def _path_exists(self, path):
        redis = await self._sentinel.master_for(self.service_name, socket_timeout=self.socket_timeout)
        return await redis.exists(path)

    def _on_prepare(self):
        pass
