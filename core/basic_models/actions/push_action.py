# coding: utf-8
from copy import copy
from typing import Union, Dict, List, Any, Optional

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate
from scenarios.user.user_model import User
from smart_kit.request.kafka_request import SmartKitKafkaRequest

PUSH_NOTIFY = "PUSH_NOTIFY"


class PushAction(StringAction):
    """
        Action для отправки пуш уведомлений в сервис пушей.
        Example:
        {
          "push_advertising_offer": {
            "type": "push",
            "surface": "COMPANION", // не обязательное, по дефолту "COMPANION", без шаблонной генерации
            "push_data": {
                "notificationHeader": "{% if day_time = 'morning' %}Время завтракать!{% else %}Хотите что нибудь заказать?{% endif %}",
                "fullText": "В нашем магазине большой ассортимент{% if day_time = 'evening' %}. Успей заказать!{% endif %}",
                "mobileAppParameters": {
                    "DeeplinkAndroid": "{[ deep_link_url }}",
                    "DeeplinkIos": "{{ deep_link_url }}",
                    "Logo": "{{ icon_url }}"
                }
            }
          }
        }
    """

    DEFAULT_REQUEST_DATA = {
        "topic_key": "push",
        "kafka_key": "main",
        SmartKitKafkaRequest.KAFKA_EXTRA_HEADERS: None
    }
    DEFAULT_EXTRA_HEADERS = {
        "request-id": "{{ uuid4() }}",
        "sender-id": "{{ uuid4() }}",
        "simple": "true"
    }
    COMPANION = "COMPANION"
    EX_HEADERS_NAME = SmartKitKafkaRequest.KAFKA_EXTRA_HEADERS

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        request_data = items.get("request_data") or self.DEFAULT_REQUEST_DATA
        request_data[self.EX_HEADERS_NAME] = request_data.get(self.EX_HEADERS_NAME) or self.DEFAULT_EXTRA_HEADERS
        self.surface = items.get("surface", self.COMPANION)
        items["request_data"] = request_data
        items["command"] = PUSH_NOTIFY
        items["nodes"] = items.get("push_data") or {}
        super().__init__(items, id)

    def _render_request_data(self, action_params):
        # копируем прежде чем рендерить шаблон хэдеров, чтобы не затереть его
        request_data = copy(self.request_data)
        request_data[self.EX_HEADERS_NAME] = {
            key: UnifiedTemplate(value).render(action_params)
            for key, value in request_data.get(self.EX_HEADERS_NAME).items()
        }
        return request_data

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        params = params or {}
        command_params = {
            "surface": self.surface,
            "content": self._generate_command_context(user, text_preprocessing_result, params),
            "project_id": user.settings["template_settings"]["project_id"]
        }
        requests_data = self._render_request_data(params)
        commands = [Command(self.command, command_params, self.id, request_type=self.request_type,
                            request_data=requests_data)]
        return commands
