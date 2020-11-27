from unittest import TestCase
from core.basic_models.actions.command import Command


class TestCommand(TestCase):
    def test_1(self):
        expected = {"message_name": "my_name", "payload": {}}

        command = Command("my_name")
        result = command.raw

        self.assertDictEqual(expected, result)

    def test_2(self):
        expected = {"message_name": "my_name", "payload": {"id": 5}}

        command = Command("my_name", {"id": 5})
        result = command.raw

        self.assertDictEqual(expected, result)
