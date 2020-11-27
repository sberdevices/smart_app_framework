from typing import Dict, Any

from confluent_kafka.cimpl import Message
from opentracing import Span

from core.jaeger_custom_client.jaeger_config import KAFKA_MAP
from core.message.from_message import SmartAppFromMessage
import core.message.message_constants as const


def get_incoming_spam(tracer, from_message: SmartAppFromMessage, mq_message: Message) -> Span:
    """
    Метод извлекает информацию об trace из входящего сообщения кафки. Созданный Span
    обогащается тегами
    :param tracer: Трейсер
    :param from_message: Распарщенное сообщение
    :param mq_message: Сообщение из кафки
    :return: Проинициализированный и активированный Span
    """
    span_context = tracer.extract(KAFKA_MAP, mq_message)
    span = tracer.start_span(
        operation_name=from_message.type,
        child_of=span_context)
    params = build_log_params(from_message)
    for key, value in params.items():
        span.set_tag(key, value)
    return span


def build_log_params(from_message: SmartAppFromMessage) -> Dict[str, Any]:
    logging_dict = {
        const.MSG_MESSAGEID_KEY: from_message.incremental_id,
        const.MSG_USERCHANNEL_KEY: from_message.channel,
        const.MSG_USERID_KEY: from_message.uid
    }
    chat_id = getattr(from_message, "chat_id", None)
    if chat_id:
        logging_dict[const.MSG_CHATID_KEY] = chat_id
    return logging_dict
