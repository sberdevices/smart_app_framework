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

    def open(self, filename, *args, **kwargs):
        return self._run(self._open, filename, *args, **kwargs)

    def glob(self, path, pattern):
        return self._run(self._glob, path, pattern)

    def path_exists(self, path):
        return self._run(self._path_exists, path)

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
