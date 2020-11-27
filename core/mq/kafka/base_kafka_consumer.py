# coding: utf-8


class BaseKafkaConsumer:
    def subscribe(self, topics=None):
        raise NotImplementedError

    def poll(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
