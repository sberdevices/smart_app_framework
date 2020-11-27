# coding: utf-8
import random

import pyignite
from pyignite.exceptions import ReconnectError, SocketError

import core.logging.logger_constants as log_const
from core.db_adapter import error
from core.db_adapter.db_adapter import DBAdapter
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring


class IgniteAdapter(DBAdapter):

    def __init__(self, config):
        self._init_params = config.get("init_params", {})
        self._url = config["url"]
        if config.get("randomize_url"):
            random.shuffle(self._url)
        self._cache_name = config["cache_name"]
        self._cache = None
        super(IgniteAdapter, self).__init__(config)

    def _open(self, filename, *args, **kwargs):
        pass

    def _list_dir(self, path):
        raise error.NotSupportedOperation

    def _glob(self, path, pattern):
        raise error.NotSupportedOperation

    def _path_exists(self, path):
        raise error.NotSupportedOperation

    def connect(self):
        try:
            self._client = pyignite.Client(**self._init_params)
            self._client.connect(self._url)
            self._cache = self._client.get_or_create_cache(self._cache_name)
            logger_args = {
                log_const.KEY_NAME: log_const.IGNITE_VALUE,
                "pyignite_args": str(self._init_params),
                "pyignite_addresses": str(self._url)
            }
            log("IgniteAdapter to servers %(pyignite_addresses)s created", params=logger_args, level="WARNING")
        except Exception:
            log("IgniteAdapter connect error",
                          params={log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE},
                          level="ERROR",
                          exc_info=True)
            monitoring.got_counter("ignite_connection_exception")
            raise

    def _save(self, id, data):
        return self.cache.put(id, data)

    def _replace_if_equals(self, id, sample, data):
        return self._cache.replace_if_equals(id, sample, data)

    def _get(self, id):
        data = self.cache.get(id)
        return data

    @property
    def cache(self):
        if self._cache is None:
            log('Attempt to recreate ignite instance', level="WARNING")
            self.connect()
            monitoring.got_counter("ignite_reconnection")
        return self._cache

    @property
    def _handled_exception(self):
        # TypeError is raised during reconnection if all nodes are exhausted
        return OSError, SocketError, ReconnectError

    def _on_prepare(self):
        self._cache = None

    def _get_counter_name(self):
        return "ignite_adapter"
