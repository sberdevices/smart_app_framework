from core.request.base_request import BaseRequest


class KafkaRequest(BaseRequest):
    TOPIC_KEY = "topic_key"
    KAFKA_KEY = "kafka_key"

    def __init__(self, items, id=None):
        super(KafkaRequest, self).__init__(items)
        items = items or {}
        self.topic_key = items.get(self.TOPIC_KEY)
        self.kafka_key = items.get(self.KAFKA_KEY)

    def update_empty_items(self, items):
        self.topic_key = self.topic_key or items["topic_key"]
        self.kafka_key = self.kafka_key or items["kafka_key"]

    @property
    def group_key(self):
        return "{}_{}".format(self.kafka_key, self.topic_key) if (self.topic_key and self.kafka_key) else None

    def _get_new_headers(self, source_mq_message):
        headers = source_mq_message.headers() or []
        return headers

    def run(self, data, params=None):
        publishers = params["publishers"]
        publisher = publishers[self.kafka_key]
        source_mq_message = params["mq_message"]
        publisher.send(data, source_mq_message.key(), self.topic_key, headers=self._get_new_headers(source_mq_message))

    def __str__(self):
        return f"KafkaRequest: topic_key={self.topic_key} kafka_key={self.kafka_key}"
