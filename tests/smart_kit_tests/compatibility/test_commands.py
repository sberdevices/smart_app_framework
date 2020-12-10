import unittest
from unittest.mock import Mock, patch

from core.names import field
from smart_kit.compatibility import commands
from smart_kit.names import message_names


def patch_get_app_config(mock_get_app_config, auto_listening):
    result = Mock()
    result.AUTO_LISTENING = auto_listening
    mock_get_app_config.return_value = result


class CombineAnswerToUserTest(unittest.TestCase):
    @patch('smart_kit.configs.get_app_config')
    def test_pronounce_but_config(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config, False)
        command_1 = Mock('Command')
        command_1.name = message_names.ANSWER_TO_USER
        command_1.request_type = 'a'
        command_1.request_data = 'b'
        command_1.payload = {
            field.PRONOUNCE_TEXT: "some_text",
        }

        command_2 = Mock('Command')
        command_2.name = message_names.ANSWER_TO_USER
        command_2.request_type = 'a'
        command_2.request_data = 'b'
        command_2.payload = {
            field.PRONOUNCE_TEXT: "some_text",
        }

        command_3 = Mock('Command')
        command_3.name = message_names.ANSWER_TO_USER
        command_3.request_type = 'a'
        command_3.request_data = 'b'
        command_3.payload = {
            field.PRONOUNCE_TEXT: "some_text",
        }

        list_of_commands = [command_1, command_2, command_3]
        user = Mock()
        result = commands.combine_commands(list_of_commands, user)
        self.assertFalse(result[0].payload[field.AUTO_LISTENING])

    @patch('smart_kit.configs.get_app_config')
    def test_pronounce_but_scenario(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config, False)
        command_1 = Mock('Command')
        command_1.name = message_names.ANSWER_TO_USER
        command_1.request_type = 'a'
        command_1.request_data = 'b'
        command_1.payload = {
            field.PRONOUNCE_TEXT: "some_text",
        }

        command_2 = Mock('Command')
        command_2.name = message_names.ANSWER_TO_USER
        command_2.request_type = 'a'
        command_2.request_data = 'b'
        command_2.payload = {
            field.PRONOUNCE_TEXT: "some_text",
            field.AUTO_LISTENING: False
        }

        command_3 = Mock('Command')
        command_3.name = message_names.ANSWER_TO_USER
        command_3.request_type = 'a'
        command_3.request_data = 'b'
        command_3.payload = {
            field.PRONOUNCE_TEXT: "some_text",
            field.AUTO_LISTENING: True
        }

        list_of_commands = [command_1, command_2, command_3]
        user = Mock()
        result = commands.combine_commands(list_of_commands, user)

        self.assertFalse(result[0].payload[field.AUTO_LISTENING])

    @patch('smart_kit.configs.get_app_config')
    def test_pronounce(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config, True)
        command_1 = Mock('Command')
        command_1.name = message_names.ANSWER_TO_USER
        command_1.request_type = 'a'
        command_1.request_data = 'b'
        command_1.payload = {
            field.PRONOUNCE_TEXT: "some_text",
        }

        command_2 = Mock('Command')
        command_2.name = message_names.ANSWER_TO_USER
        command_2.request_type = 'a'
        command_2.request_data = 'b'
        command_2.payload = {
            field.PRONOUNCE_TEXT: "some_text",
        }

        command_3 = Mock('Command')
        command_3.name = message_names.ANSWER_TO_USER
        command_3.request_type = 'a'
        command_3.request_data = 'b'
        command_3.payload = {
            field.PRONOUNCE_TEXT: "some_text",
        }

        list_of_commands = [command_1, command_2, command_3]
        user = Mock()
        result = commands.combine_commands(list_of_commands, user)

        self.assertTrue(result[0].payload[field.AUTO_LISTENING])

    @patch('smart_kit.configs.get_app_config')
    def test_no_pronounce_but_scenario(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config, True)
        command_1 = Mock('Command')
        command_1.name = message_names.ANSWER_TO_USER
        command_1.request_type = 'a'
        command_1.request_data = 'b'
        command_1.payload = {
            field.AUTO_LISTENING: True
        }

        command_2 = Mock('Command')
        command_2.name = message_names.ANSWER_TO_USER
        command_2.request_type = 'a'
        command_2.request_data = 'b'
        command_2.payload = {
            field.AUTO_LISTENING: False
        }

        command_3 = Mock('Command')
        command_3.name = message_names.ANSWER_TO_USER
        command_3.request_type = 'a'
        command_3.request_data = 'b'
        command_3.payload = {}

        list_of_commands = [command_1, command_2, command_3]
        user = Mock()
        result = commands.combine_commands(list_of_commands, user)

        self.assertTrue(result[0].payload[field.AUTO_LISTENING])

    @patch('smart_kit.configs.get_app_config')
    def test_no_pronounce_but_config(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config, True)
        command_1 = Mock('Command')
        command_1.name = message_names.ANSWER_TO_USER
        command_1.request_type = 'a'
        command_1.request_data = 'b'
        command_1.payload = {
        }

        command_2 = Mock('Command')
        command_2.name = message_names.ANSWER_TO_USER
        command_2.request_type = 'a'
        command_2.request_data = 'b'
        command_2.payload = {
        }

        command_3 = Mock('Command')
        command_3.name = message_names.ANSWER_TO_USER
        command_3.request_type = 'a'
        command_3.request_data = 'b'
        command_3.payload = {
        }

        list_of_commands = [command_1, command_2, command_3]
        user = Mock()
        result = commands.combine_commands(list_of_commands, user)

        self.assertTrue(result[0].payload[field.AUTO_LISTENING])

    @patch('smart_kit.configs.get_app_config')
    def test_no_pronounce(self, mock_get_app_config):
        patch_get_app_config(mock_get_app_config, False)
        command_1 = Mock('Command')
        command_1.name = message_names.ANSWER_TO_USER
        command_1.request_type = 'a'
        command_1.request_data = 'b'
        command_1.payload = {
        }

        command_2 = Mock('Command')
        command_2.name = message_names.ANSWER_TO_USER
        command_2.request_type = 'a'
        command_2.request_data = 'b'
        command_2.payload = {
        }

        command_3 = Mock('Command')
        command_3.name = message_names.ANSWER_TO_USER
        command_3.request_type = 'a'
        command_3.request_data = 'b'
        command_3.payload = {}

        list_of_commands = [command_1, command_2, command_3]
        user = Mock()
        result = commands.combine_commands(list_of_commands, user)

        self.assertFalse(result[0].payload[field.AUTO_LISTENING])
