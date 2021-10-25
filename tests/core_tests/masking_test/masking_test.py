from unittest import TestCase

import json
from core.message.from_message import SmartAppFromMessage


class MaskingTest(TestCase):
    def test_1(self):
        input_msg = {
            "messageId": 2,
            "uuid": {"userChannel": "B2C", "userId": "userId", "sub": "sub"},
            "payload": {
                "message": {
                    "original_text": "Номер карты 1234567890123456"
                }
            },
            "messageName": "MESSAGE_TO_SKILL"
        }

        json_input_msg = json.dumps(input_msg, ensure_ascii=False)
        message = SmartAppFromMessage(value=json_input_msg, headers=[])

        masked_message = json.loads(message.masked_value)

        self.assertEqual(masked_message['payload']['message']['original_text'], "Номер карты ************3456")

    def test_2(self):
        input_msg = {
            "messageId": 2,
            "uuid": {"userChannel": "B2C", "userId": "userId", "sub": "sub"},
            "payload": {
                "message": {
                    "original_text": "Номер карты 1234567890123456 вот"
                }
            },
            "messageName": "MESSAGE_TO_SKILL"
        }

        json_input_msg = json.dumps(input_msg, ensure_ascii=False)
        message = SmartAppFromMessage(value=json_input_msg, headers=[])

        masked_message = json.loads(message.masked_value)

        self.assertEqual(masked_message['payload']['message']['original_text'], "Номер карты ************3456 вот")

    def test_3(self):
        input_msg = {
            "messageId": 2,
            "uuid": {"userChannel": "B2C", "userId": "userId", "sub": "sub"},
            "payload": {
                "message": {
                    "original_text": "Номер карты1234567890123456 вот"
                }
            },
            "messageName": "MESSAGE_TO_SKILL"
        }

        json_input_msg = json.dumps(input_msg, ensure_ascii=False)
        message = SmartAppFromMessage(value=json_input_msg, headers=[])

        masked_message = json.loads(message.masked_value)

        self.assertEqual(masked_message['payload']['message']['original_text'], "Номер карты************3456 вот")
