# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.request import kafka_request


class RequestTest1(unittest.TestCase):
    def setUp(self):
        self.test_items1 = {"topic_key": "12345", "kafka_replyTopic": "any theme", "timeout": 10,
                           "app_callback_id": 22, "kafka_key": "54321"}  # пусть
        self.test_items2 = {"topic_key": "12345", "timeout": 10}  # пусть
        self.test_items3 = {"topic_key": "12345", "kafka_replyTopic": "any theme", "timeout": 10}  # пусть
        self.test_source_mq_message = Mock('source_mq_message')
        self.test_source_mq_message.headers = lambda: [("any header 1", 1)]

    def test_smart_kafka_request_init(self):
        obj1 = kafka_request.SmartKitKafkaRequest(self.test_items1)
        self.assertTrue(obj1.KAFKA_REPLY_TOPIC == "kafka_replyTopic")
        self.assertTrue(obj1.KAFKA_KEY == "kafka_key")
        self.assertTrue(obj1.topic_key == "12345")
        with self.assertRaises(AttributeError):
            obj2 = kafka_request.SmartKitKafkaRequest("")
        self.assertTrue(obj1._callback_id == 22)
        self.assertTrue(obj1._kafka_replyTopic == "any theme")

    def test_smart_kafka_request_callback_id_header_name(self):
        obj1 = kafka_request.SmartKitKafkaRequest(self.test_items1)
        self.assertTrue(obj1._callback_id_header_name == "app_callback_id")

    def test_smart_kafka_request_get_new_headers(self):
        obj1 = kafka_request.SmartKitKafkaRequest(self.test_items1)
        obj2 = kafka_request.SmartKitKafkaRequest(self.test_items2)
        obj3 = kafka_request.SmartKitKafkaRequest(self.test_items3)
        self.assertTrue(obj1._get_new_headers(self.test_source_mq_message) == [('any header 1', 1), (
                                                                               'app_callback_id', b'22'),
                                                                               ('kafka_replyTopic', b'any theme')])
        self.assertTrue(obj2._get_new_headers(self.test_source_mq_message) == [('any header 1', 1)])
        self.assertTrue(obj3._get_new_headers(self.test_source_mq_message) == [('any header 1', 1),
                                                                               ('kafka_replyTopic', b'any theme')])

    def test_smart_kafka_request_str(self):
        obj1 = kafka_request.SmartKitKafkaRequest(self.test_items1)
        obj2 = kafka_request.SmartKitKafkaRequest(self.test_items2)
        self.assertTrue(obj1.__str__() == "KafkaRequest: kafka_key=54321")
        self.assertTrue(obj2.__str__() == "KafkaRequest: kafka_key=None")
