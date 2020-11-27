# coding: utf-8
from smart_kit.utils.monitoring import smart_kit_metrics


class HandlerBase:
    TOPIC_KEY = "template_app"
    KAFKA_KEY = "main"

    def __init__(self, app_name):
        self.app_name = app_name

    def run(self, payload, user):
        # отправка события о входящем сообщении в систему мониторинга
        smart_kit_metrics.counter_incoming(self.app_name, user.message.message_name, self.__class__.__name__,
                                           user, app_info=user.message.app_info)
