# coding: utf-8

from core.db_adapter.os_adapter import OSAdapter
from core.logging.logger_utils import log
import core.logging.logger_constants as log_const


class BaseRepository:
    def __init__(self, source=None, key=None):
        self.source = source or OSAdapter(None)
        self._data = None
        self.key = key

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    def load(self):
        params = {
            "repository_class_name": self.__class__.__name__,
            "repository_key": self.key,
            log_const.KEY_NAME: log_const.REPOSITORY_LOAD_VALUE
        }
        log("%(repository_class_name)s.load  %(repository_key)s repo loading completed.", params=params,
                   level="WARNING")

    def fill(self, data):
        self.data = data

    def clear(self):
        self.data.clear()
        log("%(repository_class_name)s.clear %(repository_key)s cleared.",
                      params={"repository_class_name": self.__class__.__name__,
                              "repository_key": self.key,
                              log_const.KEY_NAME: log_const.REPOSITORY_CLEAR_VALUE},
                      level="WARNING")

    def save(self, save_parameters):
        raise NotImplementedError

    def check_load_in_parts(self):
        return False
