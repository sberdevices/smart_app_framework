from core.db_adapter import error
from core.db_adapter.db_adapter import DBAdapter


class MemoryAdapter(DBAdapter):

    def __init__(self, config=None):
        super(DBAdapter, self).__init__(config)
        self.memory_storage = {}

    def _glob(self, path, pattern):
        raise error.NotSupportedOperation

    def _path_exists(self, path):
        raise error.NotSupportedOperation

    def _on_prepare(self):
        pass

    def connect(self):
        pass

    def _open(self, filename, *args, **kwargs):
        pass

    def _save(self, id, data):
        self.memory_storage[id] = data

    def _replace_if_equals(self, id, sample, data):
        stored_data = self.memory_storage.get(id)
        if stored_data == sample:
            self.memory_storage[id] = data
            return True
        return False

    def _get(self, id):
        data = self.memory_storage.get(id)
        return data

    def _list_dir(self, path):
        pass
