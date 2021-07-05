import os
import time

from core.db_adapter.os_adapter import OSAdapter

import core.logging.logger_constants as log_const
from core.repositories.items_repository import ItemsRepository
from core.logging.logger_utils import log


class FileRepository(ItemsRepository):
    def __init__(self, filename, loader, source=None, save_target=None, saver=None, *args, **kwargs):
        super(FileRepository, self).__init__(source=source, *args, **kwargs)
        self.filename = filename
        self.loader = loader
        self.saver = saver
        self.save_target = save_target
        self._file_exist = False

    def load(self):
        if self.source.path_exists(self.filename):
            self._file_exist = True
            with self.source.open(self.filename, 'rb') as stream:
                binary_data = stream.read()
                data = binary_data.decode()
                self.fill(self.loader(data))
        else:
            self._file_exist = False
            params = {
                "error_repository_path": self.filename,
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log("FileRepository.load loading failed with file %(error_repository_path)s",
                params=params, level="WARNING")
        super(FileRepository, self).load()

    def save(self, save_parameters):
        with self.source.open(self.save_target, 'wb') as stream:
            stream.write(self.saver(self.data, **save_parameters).encode())


class UpdatableFileRepository(FileRepository):
    def __init__(self, *args, update_cooldown=5, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_mtime = None
        self._last_update_time = 0
        self.update_cooldown = update_cooldown
        if self.source and not isinstance(self.source, OSAdapter):
            raise Exception(f"{self.__class__.__name__} support only OSAdapter")

    @FileRepository.data.getter
    def data(self):
        if self._is_outdated:
            params = {
                "filename": self.filename
            }
            log("FileRepository.data %(filename)s is outdated. Data will be reloaded.",
                params=params, level="INFO")

            self.load()
        return self._data

    def load(self):
        super().load()
        if self._file_exist:
            self._last_mtime = self.source.mtime(self.filename)
        self._last_update_time = time.time()

    @property
    def expired(self):
        return self._last_update_time + self.update_cooldown < time.time()

    @property
    def _is_outdated(self):
        if self._file_exist and self.expired:
            return self.source.mtime(self.filename) > self._last_mtime
        return False
