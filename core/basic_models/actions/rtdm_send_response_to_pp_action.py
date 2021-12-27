# coding: utf-8
from typing import Union, Dict, List, Any, Optional

from core.basic_models.actions.basic_actions import CommandAction
from core.basic_models.actions.command import Command
from core.text_preprocessing.base import BaseTextPreprocessingResult
from scenarios.user.user_model import User


RTDM_RESPONSE = "RTDM_RESPONSE"


class RtdmSendResponseToPpAction(CommandAction):
    """
    Action отправки отклика на ПП.

    Пример:

    {
       "messageId": 10000001,
       "messageName": "RTDM_VIEWED_EVENTS",
       "userChannel": "SBOL",
       "nextSystem": "RTDM Adapter",
       "handlerName": "AI_HANDLER",
       "userId": "1594098519615",
       "chatId": "1594098487427",
       "notificationId": "1594098519616",
       "notificationCode": "CREDIT",
       "feedbackStatus": "FS",
       "description": "Клик FS"
    }
    """

    DEFAULT_REQUEST_DATA = {
        "topic_key": "CHATBOT_INPUT",
        "kafka_key": "RTDM_VIEWED_EVENTS"
    }

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.command = "RTDM_COMMAND"
        self.request_data = items.get("request_data") or self.DEFAULT_REQUEST_DATA
        self.notification_id = items["notificationId"]
        self.notification_code = items["notificationCode"]
        self.feedback_status = items["feedbackStatus"]
        self.description = items["description"]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        command_params = {
            "messageName": "RTDM_VIEWED_EVENTS",
            "userChannel": user.message.as_dict[user.message.UUID]["userChannel"],
            "nextSystem": "RTDM Adapter",
            "handlerName": "AI_HANDLER",
            "userId": user.message.as_dict[user.message.UUID]["userId"],
            "chatId": user.message.as_dict[user.message.UUID]["chatId"],
            "notificationId": self.notification_id,
            "notificationCode": self.notification_code,
            "feedbackStatus": self.feedback_status,
            "description": self.description
        }
        # Отправка отклика клиента по ПП
        commands = [Command(self.command, command_params, self.id, request_type=self.request_type,
                            request_data=self.request_data)]
        return commands
