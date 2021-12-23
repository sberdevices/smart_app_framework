# coding: utf-8
from copy import copy
from typing import Union, Dict, List, Any, Optional

from core.basic_models.actions.basic_actions import CommandAction
from core.basic_models.actions.command import Command
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate
from scenarios.user.user_model import User
from lazy import lazy

from core.message.from_message import SmartAppFromMessage
from smart_kit.message.smartapp_to_message import SmartAppToMessage


class RtdmEventAction(CommandAction):
    """
    Action обратного потока, для отправки пользовательских событий в RTDM.

    Пример::

        {
            "type": "rtdm_info_event_action",
            "notification_id": "{{ rtdm.offers[0].notificationId }}",
            "feedback_status": "FS",
            "description": "Вклад ВА ПП"
        }
    """

    DEFAULT_REQUEST_DATA = {
        "topic_key": "push",
        "kafka_key": "main"
    }

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.command = "RTDM_COMMAND"
        self.request_data = items.get("request_data") or self.DEFAULT_REQUEST_DATA
        self.channel: str = items["channel"]
        self.mode: str = items["mode"]
        self.epkId: str = items["epkId"]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        params = params or {}
        command_params = {
            "rqUid": "{{ uuid4() }}",
            "rqTm": "{{ now() }}",
            "systemName": user.settings["template_settings"]["system_name"],
            "channel": self.channel,
            "epkId": self.epkId,
            "mode": self.mode
        }
        command_params = {
            key: UnifiedTemplate(value).render(params)
            for key, value in command_params.items()
        }
        commands = [Command(self.command, command_params, self.id, request_type=self.request_type,
                            request_data=self.request_data)]
        return commands


class SmartAppRtdmToMessage(SmartAppToMessage):

    @lazy
    def as_dict(self):
        return self.payload


