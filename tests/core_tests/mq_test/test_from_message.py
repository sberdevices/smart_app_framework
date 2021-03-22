import json
from unittest import TestCase

from core.message.from_message import SmartAppFromMessage
from core.utils.utils import current_time_ms
from core.message.msg_validator import MessageValidator


class PieMessageValidator(MessageValidator):
    def validate(self, message_name: str, payload: dict):
        return 3.14 < payload.get("pi", 0) < 3.15


class TestFromMessage(TestCase):
    def test_1(self):
        input_msg = {
            "messageId": 2,
            "uuid": {"userChannel": "B2C", "userId": "userId", "sub": "sub"},
            "payload": {
                "message": {
                    "original_text": "сверни приложение"
                },
                "device": {
                    "platformType": "android",
                    "platformVersion": "9",
                    "surface": "STARGATE",
                    "surfaceVersion": "1.56.20200828144304",
                    "features": {"appTypes": ["APK", "WEB_APP", "DIALOG"]},
                    "capabilities": {"mic": {"available": True},
                                     "screen": {"available": True},
                                     "speak": {"available": True}},
                    "deviceId": "34534545345345",
                    "deviceManufacturer": "SberDevices",
                    "deviceModel": "stargate",
                    "additionalInfo": {}
                }
            },
            "messageName": "MESSAGE_TO_SKILL"
        }
        json_input_msg = json.dumps(input_msg, ensure_ascii=False)
        topic = "test"
        headers = []
        current_time = current_time_ms()
        message = SmartAppFromMessage(value=json_input_msg, topic_key=topic, headers=headers, creation_time=current_time)

        self.assertAlmostEqual(message.creation_time, current_time)
        self.assertEqual(2, message.incremental_id)
        self.assertEqual(input_msg["uuid"]["userChannel"], message.channel)
        self.assertEqual(input_msg["messageName"], message.type)
        self.assertEqual(input_msg["uuid"]["userId"], message.uid)
        self.assertEqual(json_input_msg, message.value)
        self.assertEqual("sub_userId_B2C", message.db_uid)
        self.assertDictEqual(input_msg["uuid"], message.uuid)
        self.assertDictEqual(input_msg["payload"], message.payload)
        device = input_msg["payload"]["device"]
        self.assertEqual(device["platformType"], message.device.platform_type)
        self.assertEqual(device["platformVersion"], message.device.platform_version)
        self.assertEqual(device["surface"], message.device.surface)
        self.assertEqual(device["surfaceVersion"], message.device.surface_version)
        self.assertEqual(device["features"], message.device.features)
        self.assertEqual(device["capabilities"], message.device.capabilities)
        self.assertEqual(device["additionalInfo"], message.device.additional_info)
        self.assertEqual(topic, message.topic_key)

    def test_valid_true(self):
        input_msg = {
            "messageId": 2,
            "sessionId": 234,
            "uuid": {"userChannel": "web", "userId": 99, "chatId": 80},
            "payload": {"key": "some payload"},
            "messageName": "some_type"
        }
        json_input_msg = json.dumps(input_msg, ensure_ascii=False)
        headers = [('test_header', 'result')]
        message = SmartAppFromMessage(json_input_msg, headers=headers)
        self.assertTrue(message.validate())

    def test_valid_false(self):
        input_msg = {
            "uuid": {"userChannel": "web", "userId": 99, "chatId": 80},
            "payload": "some payload"
        }
        headers = [('test_header', 'result')]
        json_input_msg = json.dumps(input_msg, ensure_ascii=False)

        message = SmartAppFromMessage(json_input_msg, headers=headers)
        self.assertFalse(message.validate())

    def test_validation(self):
        input_msg = {
            "uuid": {"userChannel": "web", "userId": 99, "chatId": 80},
            "messageName": "some_name",
            "messageId": "random_id",
            "sessionId": "random_id",
            "payload": {
                "pi": 3.14159265358979,
            }
        }
        headers = [('test_header', 'result')]

        message = SmartAppFromMessage(
            json.dumps(input_msg, ensure_ascii=False),
            headers=headers, validators=(PieMessageValidator(),))
        self.assertTrue(message.validate())

        input_msg["payload"]["pi"] = 2.7182818284
        message = SmartAppFromMessage(
            json.dumps(input_msg, ensure_ascii=False),
            headers=headers, validators=(PieMessageValidator(),))
        self.assertFalse(message.validate())
