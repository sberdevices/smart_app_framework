# coding: utf-8
from threading import Thread

import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.monitoring import monitoring
from core.mq.kafka.kafka_publisher import KafkaPublisher


class AsyncKafkaPublisher(KafkaPublisher):
    def __init__(self, config):
        super().__init__(config)
        self._cancelled = False
        self._poll_thread = Thread(target=self._poll_for_callbacks)
        self._poll_thread.start()

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
            monitoring.monitoring.got_counter("kafka_producer_exception")

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
            monitoring.monitoring.got_counter("kafka_producer_exception")

    def _poll_for_callbacks(self):
        poll_timeout = self._config.get("poll_timeout", 1)
        while not self._cancelled:
            self._producer.poll(poll_timeout)

    def close(self):
        self._producer.flush(self._config["flush_timeout"])
        self._cancelled = True
        self._poll_thread.join()
        log(f"KafkaProducer.close: producer to {self._config['topic']} flushed, poll_thread joined.")
