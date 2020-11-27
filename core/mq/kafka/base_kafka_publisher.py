# coding: utf-8


class BaseKafkaPublisher:
    def send(self, message, uid, topic):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
