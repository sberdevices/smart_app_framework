# coding: utf-8
import logging
import os
import time

from confluent_kafka import Producer

import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring
from core.mq.kafka.base_kafka_publisher import BaseKafkaPublisher


class KafkaPublisher(BaseKafkaPublisher):
    def __init__(self, config):
        self._config = config["publisher"]
        conf = self._config["conf"]
        conf["error_cb"] = self._error_callback
        conf["on_delivery"] = self._delivery_callback
        internal_log_path = self._config.get("internal_log_path")
        if internal_log_path:
            debug_logger = logging.getLogger("debug_publisher")
            timestamp = time.strftime("_%d%m%Y_")
            debug_logger.addHandler(logging.FileHandler("{}/kafka_publisher_debug{}{}.log".format(internal_log_path, timestamp, os.getpid())))
            conf["logger"] = debug_logger
        self._producer = Producer(**conf)

    def send(self, value, key=None, topic_key=None, headers=None):
        try:
            topic = self._config["topic"]
            if topic_key is not None:
                topic = topic[topic_key]
            producer_params = dict()
            if key is not None:
                producer_params["key"] = key
            self._producer.produce(topic=topic, value=value, headers=headers or [], **producer_params)
        except BufferError as e:
            params = {
                "queue_amount": len(self._producer),
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log("KafkaProducer: Local producer queue is full (%(queue_amount)s messages awaiting delivery):"
                       " try again\n", params=params, level="ERROR")
            monitoring.got_counter("kafka_producer_exception")
        self._poll()

    def send_to_topic(self, value, key=None, topic=None, headers=None):
        try:
            if topic is None:
                params = {
                    "message": str(value),
                    log_const.KEY_NAME: log_const.EXCEPTION_VALUE
                }
                log("KafkaProducer: Failed sending message %{message}s. Topic is not defined", params=params,
                              level="ERROR")
            producer_params = dict()
            if key is not None:
                producer_params["key"] = key
            self._producer.produce(topic=topic, value=value, headers=headers or [], **producer_params)
        except BufferError as e:
            params = {
                "queue_amount": len(self._producer),
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log("KafkaProducer: Local producer queue is full (%(queue_amount)s messages awaiting delivery):"
                       " try again\n", params=params, level="ERROR")
            monitoring.got_counter("kafka_producer_exception")
        self._poll()

    def _poll(self):
        poll_timeout = self._config.get("poll_timeout", 0)
        if poll_timeout > 0:
            while True:
                result = self._producer.poll(poll_timeout)
                if not result:
                    return

    def _error_callback(self, err):
        params = {
            "error": str(err),
            log_const.KEY_NAME: log_const.EXCEPTION_VALUE
        }
        log("KafkaProducer: Error: %(error)s", params=params, level="ERROR")
        monitoring.got_counter("kafka_producer_exception")

    def _delivery_callback(self, err, msg):
        if err:
            message_text = msg.value()
            try:
                message_text = message_text.decode("utf-8")
                log("KafkaProducer: Message %(message)s send failed: %(error)s",
                              params={
                                  "message": str(message_text),
                                  "error": str(err),
                                  log_const.KEY_NAME: log_const.EXCEPTION_VALUE},
                              level="ERROR")
            except UnicodeDecodeError:
                log("KafkaProducer: %(text)s: %(error)s",
                              params={"text": f"Can't decode: {str(message_text)}",
                                      "error": err,
                                      log_const.KEY_NAME: log_const.EXCEPTION_VALUE},
                              level="ERROR",
                              exc_info=True)
            monitoring.got_counter("kafka_producer_exception")

    def close(self):
        self._producer.flush(self._config["flush_timeout"])
