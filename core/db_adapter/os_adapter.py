import io
import os
import fnmatch

from core.db_adapter.db_adapter import DBAdapter
from core.db_adapter import error


class OSAdapter(DBAdapter):
    def _save(self, id, data):
        raise error.NotSupportedOperation

    def _replace_if_equals(self, id, sample, data):
        raise error.NotSupportedOperation

    def _get(self, id):
        raise error.NotSupportedOperation

    def connect(self):
        pass

    def _on_prepare(self):
        pass

    @property
    def source(self):
        return self

    def _list_dir(self, path):
        result = []
        for path, subdirs, files in os.walk(path):
            result.extend([os.path.join(path, name) for name in files if not name.startswith(".")])
        return result

    def _open(self, filename, *args, **kwargs):
        return io.open(filename, *args, **kwargs)

    def _get_counter_name(self):
        return "os_adapter"

    def _glob(self, path, pattern):
        files_list = self._list_dir(path)
        filtered = fnmatch.filter(files_list, pattern)
        return filtered

    def _path_exists(self, path):
        return os.path.exists(path)
