# coding: utf-8
import unittest
from smart_kit.configs import logger_config


class ConfigsTest1(unittest.TestCase):
    def test_LoggerConfig(self):
        obj = logger_config.LoggerConfig("./testing/data")
        self.assertTrue(obj.config_path == "./testing/data")
        self.assertTrue(obj.repositories[0].key == 'logging_config')
        self.assertTrue(obj.repositories[0].filename == "./testing/data/logging_config.yml")
        self.assertTrue(obj._subfolder == "./testing/data")
