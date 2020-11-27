# coding: utf-8
import os

import yaml

from core.configs.base_config import BaseConfig
from core.repositories.file_repository import FileRepository
from smart_kit.utils.logger_writer.logger_formatter import SmartKitJsonFormatter

SmartKitJsonFormatter.VERSION = os.getenv("VERSION") or 0

LOGGING_CONFIG = "logging_config"


class LoggerConfig(BaseConfig):
    def __init__(self, config_path):
        self.config_path = config_path
        super(LoggerConfig, self).__init__()
        self.repositories = [
            FileRepository(self.subfolder_path("logging_config.yml"),
                           loader=yaml.safe_load, key=LOGGING_CONFIG)
        ]

    @property
    def _subfolder(self):
        return self.config_path
