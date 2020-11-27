from unittest import TestCase
from unittest.mock import Mock


from core.message.to_message import ToMessage


class Command:
    def __init__(self, name, payload=None, action_id=None):
        self.name = name
        self.payload = payload or {}
        self.action_id = action_id

    @property
    def raw(self):
        message = {"message_name": self.name, "payload": self.payload}
        if self.action_id is not None:
            message["action_id"] = self.action_id
        return message


class TestToMessage(TestCase):
    def setUp(self):
        self.mock_message = Mock()
        self.mock_message.incremental_id = 2
        self.mock_message.uuid = 123
        self.mock_message.channel = "TEST_CHANNEL"
        self.mock_message.payload = {"a": "b", "c": "d", "e": "f"}

    def test_1(self):
        expected = {
            "messageId": 2,
            "ai_version": "",
            "messages": [
                {
                    "message_name": "cmd_name",
                    "payload": {
                        "e": "f",
                        "a": "b",
                        "message": "word1"
                    }
                },
                {
                    "message_name": "cmd_name",
                    "payload": {
                        "e": "f",
                        "a": "b",
                        "message": "word2"
                    }
                }
            ],
            "uuid": 123
        }

        mock_command1 = Command(name="cmd_name", payload={"message": "word1"})
        mock_command2 = Command(name="cmd_name", payload={"message": "word2"})
        fields_to_copy_from_payload = {
            "TEST_CHANNEL": {"include_fields": ["a", "e"], "for_command_names": ["cmd_name"]}
        }

        message = ToMessage([mock_command1, mock_command2], self.mock_message, "test_topic",
                            fields_to_copy_from_payload)
        result = message.as_dict
        self.assertEqual(expected, result)
