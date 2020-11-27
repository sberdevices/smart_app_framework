import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.repositories.shard_repository import ShardRepository


class FolderRepository(ShardRepository):

    def __init__(self, path, loader, source=None, *args, **kwargs):
        super(FolderRepository, self).__init__(path, loader, source, *args, **kwargs)

    def _load_item(self, name):
        try:
            with self.source.open(name, mode='rb') as shard_stream:
                shard_binary_data = shard_stream.read()
                shard_data = shard_binary_data.decode()
                loaded_data = self.loader(shard_data)
        except:
            params = {
                "error_repository_path": str(self.path),
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log("FolderRepository.__load_item loading failed with file %(error_repository_path)s",
                          params=params,
                          level="WARNING")
            raise
        return loaded_data

    def _form_file_upload_map(self, shard_desc):
        filename_to_data = {}
        for shard in shard_desc:
            shard_data = self._load_item(shard)
            if shard_data:
                filename_to_data.update({shard: shard_data})
        return filename_to_data

    def load(self):
        shard_desc = self.get_shard_desc()
        self.fill(self._form_file_upload_map(shard_desc))
        super(FolderRepository, self).load()

    def load_in_parts(self, count):
        self.clear()
        shard_desc = self.get_shard_desc()
        for i in range(0, len(shard_desc), count):
            desc_slice = shard_desc[i: i + count]
            self.fill_on_top(self._form_file_upload_map(desc_slice))
            log("FolderRepository.load_in_parts start loading [%(current_count)s/%(all_count)s]",
                          params={"current_count": i + len(desc_slice),
                                  "all_count": len(shard_desc)},
                          level="WARNING")
            super(FolderRepository, self).load()

    def get_shard_desc(self):
        shard_desc = self.source.list_dir(self.path)
        if len(shard_desc) == 0:
            params = {
                "error_repository_path": self.path,
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log("FolderRepository.load got empty or nonexistent folder path %(error_repository_path)s",
                          params=params, level="WARNING")
        return shard_desc

    def check_load_in_parts(self):
        return True
