from core.repositories.items_repository import ItemsRepository
from core.logging.logger_utils import log
import core.logging.logger_constants as log_const


class FileRepository(ItemsRepository):
    def __init__(self, filename, loader, source=None, save_target=None, saver=None, *args, **kwargs):
        super(FileRepository, self).__init__(source=source, *args, **kwargs)
        self.filename = filename
        self.loader = loader
        self.saver = saver
        self.save_target = save_target

    def load(self):
        if self.source.path_exists(self.filename):
            with self.source.open(self.filename, 'rb') as stream:
                binary_data = stream.read()
                data = binary_data.decode()
                self.fill(self.loader(data))
        else:
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

