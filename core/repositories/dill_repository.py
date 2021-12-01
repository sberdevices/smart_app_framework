# coding: utf-8
import dill

import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.repositories.base_repository import BaseRepository


class DillRepository(BaseRepository):
    """
    load unpickleable file
    Args:
        filename: path to the file
        source: file adapter e.g OSAdapter, CephAdapter etc
        required: raise FileNotFoundError if file not found
    """
    def __init__(self, filename, source=None, required=True, *args, **kwargs):
        super(DillRepository, self).__init__(source=source, *args, **kwargs)
        self.filename = filename
        self.required = required

    def load(self):
        dill._dill._reverse_typemap['ClassType'] = type
        try:

            with self.source.open(self.filename, 'rb') as stream:
                data = dill.load(stream)
                self.fill(data)
        except FileNotFoundError as error:
            params = {
                'error': str(error),
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log('DillRepository.load loading failed. Error %(error)s', params=params, level='WARNING')
            if self.required:
                raise
        super(DillRepository, self).load()
