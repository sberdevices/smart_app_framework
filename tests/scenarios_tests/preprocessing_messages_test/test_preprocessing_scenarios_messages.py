import unittest
from unittest.mock import Mock

from scenarios.user.preprocessing_messages.prepricessing_messages_for_scenarios import \
    PreprocessingScenariosMessages


class PreprocessingScenariosMessagesTest(unittest.TestCase):

    def test_add_1(self):
        user = Mock()
        items = None
        description = Mock()
        description.max_message_count = 3
        description.lifetime = 10
        preprocessing_messages = PreprocessingScenariosMessages(items, description, user)
        text_preprocessing_result = Mock()
        text_preprocessing_result.raw = {"test": 123}
        preprocessing_messages.add(text_preprocessing_result)
        self.assertEqual([item for item in preprocessing_messages.processed_items], [{"test": 123}])

    def test_add_2(self):
        user = Mock()
        items = [{"ts": 35343820800, "message": {"test": 567}, "direction": "incoming"}]
        description = Mock()
        description.max_message_count = 3
        description.lifetime = 10
        preprocessing_messages = PreprocessingScenariosMessages(items, description, user)
        text_preprocessing_result = Mock()
        text_preprocessing_result.raw = {"test": 123}
        preprocessing_messages.add(text_preprocessing_result)
        self.assertListEqual([item for item in preprocessing_messages.processed_items], [{"test": 123}, {"test": 567}])

    def test_add_3(self):
        user = Mock()
        items = [{"ts": 35343820800, "message": {"test": 567}, "direction": "incoming"}]
        description = Mock()
        description.max_message_count = 1
        description.lifetime = 10
        preprocessing_messages = PreprocessingScenariosMessages(items, description, user)
        text_preprocessing_result = Mock()
        text_preprocessing_result.raw = {"test": 123}
        preprocessing_messages.add(text_preprocessing_result)
        self.assertListEqual([item for item in preprocessing_messages.processed_items], [{"test": 123}])

    def test_clear(self):
        user = Mock()
        items = [{"ts": 35343820800, "message": {"test": 567}, "direction": "incoming"}]
        description = Mock()
        description.max_message_count = 1
        description.lifetime = 10
        preprocessing_messages = PreprocessingScenariosMessages(items, description, user)
        preprocessing_messages.clear()
        self.assertListEqual([item for item in preprocessing_messages.processed_items], [])
