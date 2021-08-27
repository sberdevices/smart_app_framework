# coding: utf-8

import logging
import os
import time
import uuid

from confluent_kafka import Consumer, TIMESTAMP_NOT_AVAILABLE
from confluent_kafka.cimpl import KafkaError, KafkaException, OFFSET_END, Message as KafkaMessage

import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring
from core.mq.kafka.base_kafka_consumer import BaseKafkaConsumer


class KafkaConsumer(BaseKafkaConsumer):
    def __init__(self, config):
        self._config = config["consumer"]
        self.assign_offset_end = self._config.get("assign_offset_end", False)
        conf = self._config["conf"]
        conf.setdefault("group.id", str(uuid.uuid1()))
        self.autocommit_enabled = conf.get("enable.auto.commit", True)
        internal_log_path = self._config.get("internal_log_path")
        conf["error_cb"] = self._error_callback
        if internal_log_path:
            debug_logger = logging.getLogger("debug_consumer")
            timestamp = time.strftime("_%d%m%Y_")
            debug_logger.addHandler(logging.FileHandler(
                "{}/kafka_consumer_debug{}{}.log".format(internal_log_path, timestamp, os.getpid())))
            conf["logger"] = debug_logger
        self._consumer = Consumer(**conf)

    @staticmethod
    def on_assign_offset_end(consumer, partitions):
        for p in partitions:
            p.offset = OFFSET_END
        KafkaConsumer.on_assign_log(consumer, partitions)
        consumer.assign(partitions)

    @staticmethod
    def on_coop_assign_offset_end(consumer, partitions):
        for p in partitions:
            p.offset = OFFSET_END
        KafkaConsumer.on_assign_log(consumer, partitions)
        consumer.incremental_assign(partitions)

    @staticmethod
    def on_assign_log(consumer, partitions):
        log_level = "WARNING"
        for p in partitions:
            if p.error:
                log_level = "ERROR"
        params = {
            "partitions": partitions,
            log_const.KEY_NAME: log_const.KAFKA_ON_ASSIGN_VALUE,
            "log_level": log_level
        }
        log("KafkaConsumer.subscribe<on_assign>: assign %(partitions)s %(log_level)s", params=params, level=log_level)

    def subscribe(self, topics=None):
        topics = topics or list(self._config["topics"].values())

        self._consumer.subscribe(topics,
                                 on_assign=self.get_on_assign_callback() if self.assign_offset_end else KafkaConsumer.on_assign_log)

    def get_on_assign_callback(self):
        if "cooperative" in self._config["conf"].get("partition.assignment.strategy", ""):
            callback = KafkaConsumer.on_coop_assign_offset_end
        else:
            callback = KafkaConsumer.on_assign_offset_end
        return callback

    def unsubscribe(self):
        self._consumer.unsubscribe()

    def poll(self):
        msg = self._consumer.poll(self._config["poll_timeout"])
        if msg is not None:
            return self._process_message(msg)

    def consume(self, num_messages: int = 1):
        messages = self._consumer.consume(num_messages=num_messages, timeout=self._config["poll_timeout"])
        for msg in messages:
            yield self._process_message(msg)

    def commit_offset(self, msg):
        if msg is not None:
            if self.autocommit_enabled:
                self._consumer.store_offsets(msg)
            else:
                self._consumer.commit(msg, **{"async": False})

    def get_msg_create_time(self, mq_message):
        timestamp_type, timestamp = mq_message.timestamp()
        return timestamp if timestamp_type is not TIMESTAMP_NOT_AVAILABLE else None

    def _error_callback(self, err):
        params = {
            "error": str(err),
            log_const.KEY_NAME: log_const.EXCEPTION_VALUE
        }
        log("KafkaConsumer: Error: %(error)s", params=params, level="WARNING")
        monitoring.got_counter("kafka_consumer_exception")

    # noinspection PyMethodMayBeStatic
    def _process_message(self, msg: KafkaMessage):
        err = msg.error()
        if err:
            if err.code() == KafkaError._PARTITION_EOF:
                return None
            else:
                monitoring.got_counter("kafka_consumer_exception")
                params = {
                    "code": err.code(),
                    "pid": os.getpid(),
                    "topic": msg.topic(),
                    "partition": msg.partition(),
                    "offset": msg.offset(),
                    log_const.KEY_NAME: log_const.EXCEPTION_VALUE
                }
                log(
                    "KafkaConsumer Error %(code)s at pid %(pid)s: topic=%(topic)s partition=[%(partition)s] "
                    "reached end at offset %(offset)s\n", params=params, level="WARNING")
                raise KafkaException(err)

        if msg.value():
            if msg.headers() is None:
                msg.set_headers([])
            return msg

    def close(self):
        self._consumer.close()
