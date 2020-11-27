# coding: utf-8
from datetime import datetime
from pythonjsonlogger import jsonlogger

from core.model.factory import build_factory
from core.model.registered import Registered

loggers_formatter = Registered()

loggers_formatter_factory = build_factory(loggers_formatter)


class BaseJsonFormatter(jsonlogger.JsonFormatter):
    VERSION = 0
    DEV_TEAM = "NA"
    APPLICATION_NAME = "NA"

    def add_fields(self, log_record, record, message_dict):
        super(BaseJsonFormatter, self).add_fields(log_record, record, message_dict)
        dt = datetime.fromtimestamp(record.created)
        st = dt.strftime("%Y-%m-%dT%H:%M:%S")
        log_record['timestamp'] = "%s.%06d" % (st, record.msecs * 1000)
        log_record['version'] = self.VERSION
        log_record['team'] = self.DEV_TEAM
        log_record['application'] = self.APPLICATION_NAME
        if isinstance(record.args, dict):
            log_record['args'] = record.args
