# coding: utf-8
from core.model.factory import build_factory
from core.model.registered import Registered
from core.monitoring.monitoring import monitoring
from core.utils.rerunable import Rerunable

db_adapters = Registered()
db_adapter_factory = build_factory(db_adapters)


class DBAdapterException(Exception):
    pass


class DBAdapter(Rerunable):
    def __init__(self, config=None):
        super(DBAdapter, self).__init__(config)
        self._client = None

    async def _on_prepare(self):
        raise NotImplementedError

    async def connect(self):
        raise NotImplementedError

    async def _open(self, filename, *args, **kwargs):
        raise NotImplementedError

    async def _save(self, id, data):
        raise NotImplementedError

    async def _replace_if_equals(self, id, sample, data):
        raise NotImplementedError

    async def _get(self, id):
        raise NotImplementedError

    async def _list_dir(self, path):
        raise NotImplementedError

    async def _glob(self, path, pattern):
        raise NotImplementedError

    async def _path_exists(self, path):
        raise NotImplementedError

    async def _mtime(self, path):
        raise NotImplementedError

    async def open(self, filename, *args, **kwargs):
        return await self._run(self._open, filename, *args, **kwargs)

    async def glob(self, path, pattern):
        return await self._run(self._glob, path, pattern)

    async def path_exists(self, path):
        return await self._run(self._path_exists, path)

    async def mtime(self, path):
        return await self._run(self._mtime, path)

    @monitoring.got_histogram("save_time")
    async def save(self, id, data):
        return await self._run(self._save, id, data)

    @monitoring.got_histogram("save_time")
    async def replace_if_equals(self, id, sample, data):
        return await self._run(self._replace_if_equals, id, sample, data)

    @monitoring.got_histogram("get_time")
    async def get(self, id):
        return await self._run(self._get, id)

    async def list_dir(self, path):
        return await self._run(self._list_dir, path)

    @property
    async def _handled_exception(self):
        return Exception

    async def _on_all_tries_fail(self):
        raise
