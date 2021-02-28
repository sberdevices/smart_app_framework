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
