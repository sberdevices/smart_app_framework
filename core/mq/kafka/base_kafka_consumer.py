# coding: utf-8


class BaseKafkaConsumer:
    def subscribe(self, topics=None):
        raise NotImplementedError

    def poll(self):
        raise NotImplementedError

    def consume(self, num_messages=1):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
