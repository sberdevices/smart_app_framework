import io

from core.db_adapter.ceph.ceph_exception import CephIOMaxRetryReached, CephIOFileNotFoundException
from core.utils.rerunable import Rerunable


class CephIO(Rerunable):
    def __init__(self, config):
        super(CephIO, self).__init__(config)
        self.bucket = config["bucket"]
        self.filename = config["filename"]
        self.mode = config["mode"]

    @property
    def _handled_exception(self):
        return ConnectionError

    def _on_prepare(self):
        pass

    def _on_all_tries_fail(self):
        raise CephIOMaxRetryReached(f"Can't get key from {self.bucket} in case of {str(self._handled_exception)}.")

    def _get_bucket_keys(self):
        return self.bucket.get_key(self.filename)

    def __enter__(self):
        key = self._run(self._get_bucket_keys)
        if key:
            data = self._run(key.get_contents_as_string)
            io_stream = None
            if self.mode == "r":
                io_stream = io.StringIO(data.decode("utf-8"))
            elif self.mode == "rb":
                io_stream = io.BytesIO(data)
            return io_stream
        else:
            raise CephIOFileNotFoundException(f"{self.filename} is not exist.")

    def __exit__(self, type, value, traceback):
        pass
