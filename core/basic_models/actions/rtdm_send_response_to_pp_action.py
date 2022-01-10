# coding: utf-8
from typing import Union, Dict, List, Any, Optional

from core.basic_models.actions.basic_actions import CommandAction
from core.basic_models.actions.command import Command
from core.text_preprocessing.base import BaseTextPreprocessingResult
from scenarios.user.user_model import User


RTDM_RESPONSE = "RTDM_RESPONSE"


class RtdmSendResponseToPpAction(CommandAction):
    """
    Action отправки отклика на персональное предложение (ПП) в Real-Time Decision Manager (RTDM). Аналитика:
    https://confluence.sberbank.ru/pages/viewpage.action?pageId=5786345296

    Использование::
        Обязательное поле notificationId - Идентификатор события/ПП по клиенту
        Обязательное поле notificationCode - Идентификатор события/ПП отклика
        Обязательное поле feedbackStatus - тип фидбэка:
            FS - показ ПП в канале ВА,
            FA - клиент согласился на условия ПП в канале ВА (использовал саджест или другой аналог),
            FI - клиент прошел по диплинку для оформления,
        Опциональное поле description - Дополнительный атрибут
            В случае, если feedbackStatus = FA поле следует заполнить названием саджеста или текстом из саджеста
        Название топика, в который отправляется запрос указывается в template_config.yml в поле
            direct_transport_sender_provider_topic поля rtdm.

        Пример::
            {
              "type": "rtdm_send",
              "notificationId": "1594098519616",
              "notificationCode": "CREDIT",
              "feedbackStatus": "FS",
              "description": "Клик FS"
            }
    """

    DEFAULT_REQUEST_DATA = {
        "kafka_key": "RTDM_VIEWED_EVENTS"
    }

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.command = RTDM_RESPONSE
        self.request_data = self.DEFAULT_REQUEST_DATA
        self.notification_id: str = items["notificationId"]
        self.notification_code: str = items["notificationCode"]
        self.feedback_status: str = items["feedbackStatus"]
        self.description: Optional[str] = items.get("description")

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        command_params = {
            "messageName": "RTDM_VIEWED_EVENTS",
            "nextSystem": "RTDM Adapter",
            "handlerName": "AI_HANDLER",
            "notificationId": self.notification_id,
            "notificationCode": self.notification_code,
            "feedbackStatus": self.feedback_status
        }
        if self.description:
            command_params["description"] = self.description
        self.request_data["topic_key"] = \
            user.settings["template_settings"]["rtdm"]["direct_transport_sender_provider_topic"]
        # Отправка отклика клиента по ПП
        commands = [Command(self.command, command_params, self.id, request_type=self.request_type,
                            request_data=self.request_data)]
        return commands
