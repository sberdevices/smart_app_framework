# coding: utf-8
import uuid

from aiokafka import AIOKafkaConsumer, ConsumerStoppedError


class KafkaConsumer:
    def __init__(self, config):
        self._config = config["consumer"]
        self.assign_offset_end = self._config.get("assign_offset_end", False)
        conf = self._config["conf"]
        conf.setdefault("group_id", str(uuid.uuid1()))
        self.autocommit_enabled = conf.get("enable.auto.commit", True)
        topics = ",".join(list(self._config["topics"].values()))
        self._consumer = AIOKafkaConsumer(topics, **conf)

    async def start(self):
        await self._consumer.start()

    def __aiter__(self):
        if self._consumer._closed:
            raise ConsumerStoppedError()
        return self._consumer

    async def stop(self):
        await self._consumer.stop()

    # @staticmethod
    # def on_assign_offset_end(consumer, partitions):
    #     for p in partitions:
    #         p.offset = OFFSET_END
    #     KafkaConsumer.on_assign_log(consumer, partitions)
    #     consumer.assign(partitions)
    #
    # @staticmethod
    # def on_assign_log(consumer, partitions):
    #     log_level = "WARNING"
    #     for p in partitions:
    #         if p.error:
    #             log_level = "ERROR"
    #     params = {
    #         "partitions": partitions,
    #         log_const.KEY_NAME: log_const.KAFKA_ON_ASSIGN_VALUE,
    #         "log_level": log_level
    #     }
    #     log("KafkaConsumer.subscribe<on_assign>: assign %(partitions)s %(log_level)s", params=params, level=log_level)
    #
    # def subscribe(self, topics=None):
    #     topics = topics or list(self._config["topics"].values())
    #     self._consumer.subscribe(topics, on_assign=KafkaConsumer.on_assign_offset_end if self.assign_offset_end else KafkaConsumer.on_assign_log)
    #
    # def unsubscribe(self):
    #     self._consumer.unsubscribe()
    #
    # def poll(self):
    #     msg = self._consumer.poll(self._config["poll_timeout"])
    #     if msg is not None:
    #         err = msg.error()
    #         if err:
    #             if err.code() == KafkaError._PARTITION_EOF:
    #                 return None
    #             else:
    #                 monitoring.got_counter("kafka_consumer_exception")
    #                 params = {
    #                     "code": err.code(),
    #                     "pid": os.getpid(),
    #                     "topic": msg.topic(),
    #                     "partition": msg.partition(),
    #                     "offset": msg.offset(),
    #                     log_const.KEY_NAME: log_const.EXCEPTION_VALUE
    #                 }
    #                 log(
    #                     "KafkaConsumer Error %(code)s at pid %(pid)s: topic=%(topic)s partition=[%(partition)s] "
    #                     "reached end at offset %(offset)s\n", params=params, level="WARNING")
    #                 raise KafkaException(err)
    #
    #         if msg.value():
    #             if msg.headers() is None:
    #                 msg.set_headers([])
    #             return msg
    #
    # def commit_offset(self, msg):
    #     if msg is not None:
    #         if self.autocommit_enabled:
    #             self._consumer.store_offsets(msg)
    #         else:
    #             self._consumer.commit(msg, **{"async": False})
    #
    # def get_msg_create_time(self, mq_message):
    #     timestamp_type, timestamp = mq_message.timestamp()
    #     return timestamp if timestamp_type is not TIMESTAMP_NOT_AVAILABLE else None
    #
    # def _error_callback(self, err):
    #     params = {
    #         "error": str(err),
    #         log_const.KEY_NAME: log_const.EXCEPTION_VALUE
    #     }
    #     log("KafkaConsumer: Error: %(error)s", params=params, level="ERROR")
    #     monitoring.got_counter("kafka_consumer_exception")
    #
    # def close(self):
    #     self._consumer.close()
