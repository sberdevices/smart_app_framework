import os
from logging.handlers import RotatingFileHandler


class RotatingFilePidHandler(RotatingFileHandler):

    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        pid = os.getpid()
        filename = f"{filename}.{pid}"
        super(RotatingFilePidHandler, self).__init__(filename, mode, maxBytes, backupCount, encoding, delay)
