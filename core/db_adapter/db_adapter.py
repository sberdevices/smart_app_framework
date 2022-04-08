# coding: utf-8
import asyncio

import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.model.factory import build_factory
from core.model.registered import Registered
from core.monitoring.monitoring import monitoring
from core.utils.rerunable import Rerunable

db_adapters = Registered()
db_adapter_factory = build_factory(db_adapters)


class DBAdapterException(Exception):
    pass


class DBAdapter(Rerunable):
    IS_ASYNC = False

    def __init__(self, config=None):
        super(DBAdapter, self).__init__(config)
        self._client = None

    def _on_prepare(self):
        raise NotImplementedError

    def connect(self):
        raise NotImplementedError

    def _open(self, filename, *args, **kwargs):
        raise NotImplementedError

    def _save(self, id, data):
        raise NotImplementedError

    def _replace_if_equals(self, id, sample, data):
        raise NotImplementedError

    def _get(self, id):
        raise NotImplementedError

    def _list_dir(self, path):
        raise NotImplementedError

    def _glob(self, path, pattern):
        raise NotImplementedError

    def _path_exists(self, path):
        raise NotImplementedError

    def _mtime(self, path):
        raise NotImplementedError

    def open(self, filename, *args, **kwargs):
        return self._run(self._open, filename, *args, **kwargs)

    def glob(self, path, pattern):
        return self._run(self._glob, path, pattern)

    def path_exists(self, path):
        return self._run(self._path_exists, path)

    def mtime(self, path):
        return self._run(self._mtime, path)

    @monitoring.got_histogram("save_time")
    def save(self, id, data):
        return self._run(self._save, id, data)

    @monitoring.got_histogram("save_time")
    def replace_if_equals(self, id, sample, data):
        return self._run(self._replace_if_equals, id, sample, data)

    @monitoring.got_histogram("get_time")
    def get(self, id):
        return self._run(self._get, id)

    def list_dir(self, path):
        return self._run(self._list_dir, path)

    @property
    def _handled_exception(self):
        return Exception

    def _on_all_tries_fail(self):
        raise


class AsyncDBAdapter(DBAdapter):
    IS_ASYNC = True

    async def _on_all_tries_fail(self):
        raise

    async def _save(self, id, data):
        raise NotImplementedError

    async def _replace_if_equals(self, id, sample, data):
        raise NotImplementedError

    async def _get(self, id):
        raise NotImplementedError

    async def _path_exists(self, path):
        raise NotImplementedError

    async def path_exists(self, path):
        return await self._async_run(self._path_exists, path)

    @monitoring.got_histogram("save_time")
    async def save(self, id, data):
        return await self._async_run(self._save, id, data)

    @monitoring.got_histogram("save_time")
    async def replace_if_equals(self, id, sample, data):
        return await self._async_run(self._replace_if_equals, id, sample, data)

    @monitoring.got_histogram("get_time")
    async def get(self, id):
        return await self._async_run(self._get, id)

    async def _async_run(self, action, *args, _try_count=None, **kwargs):
        if _try_count is None:
            _try_count = self.try_count
        if _try_count <= 0:
            await self._on_all_tries_fail()
        _try_count = _try_count - 1
        try:
            result = await action(*args, **kwargs) if asyncio.iscoroutinefunction(action) \
                else action(*args, **kwargs)
        except self._handled_exception as e:
            params = {
                "class_name": str(self.__class__),
                "exception": str(e),
                "try_count": _try_count,
                log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE
            }
            log("%(class_name)s run failed with %(exception)s.\n Got %(try_count)s tries left.",
                params=params,
                level="ERROR")
            self._on_prepare()
            result = await self._async_run(action, *args, _try_count=_try_count, **kwargs)
            counter_name = self._get_counter_name()
            if counter_name:
                monitoring.got_counter(f"{counter_name}_exception")
        return result
