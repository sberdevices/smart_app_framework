import csv
from core.repositories.base_repository import BaseRepository


class CSVRepository(BaseRepository):
    def __init__(self, filename, source=None, *args, **kwargs):
        super(CSVRepository, self).__init__(source=source, *args, **kwargs)
        self.filename = filename

    def load(self):
        with self.source.open(self.filename, newline='') as stream:
            reader = csv.DictReader(stream)
            data = list(reader)
            self.fill(data)
        super(CSVRepository, self).load()
