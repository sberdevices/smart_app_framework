# coding: utf-8
import datetime
import json
import requests
from uuid import uuid4
from typing import Union, Dict, List, Any, Optional

from core.basic_models.actions.basic_actions import Action
from core.basic_models.actions.command import Command
from core.text_preprocessing.base import BaseTextPreprocessingResult
from scenarios.user.user_model import User
from smart_kit.action.http import HTTPRequestAction


class RtdmGetPpAndEventsAction(Action):
    """
    Action получения персонального предложения (ПП) и событий из Real-Time Decision Manager (RTDM). Полученные данные
    сохраняются в user-переменную rtdm_get_response. Аналитика:
    https://confluence.sberbank.ru/pages/viewpage.action?pageId=5786345296

    Использование::
        Обязательное поле mode - режим сервиса. Возможные значения:
            offerParam - офферы (маркетинговые предложения из Репозитория) с текстом и тегами;
            serviceParam - сервисные с тегами;

        Пример::
            {
              "type": "rtdm_get",
              "mode": "offerParam,serviceParam"
            }
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.mode: str = items["mode"]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        command_params = {
            "rqUid": user.message.incremental_id,
            "rqTm": datetime.datetime.utcnow().replace(microsecond=0).isoformat(),
            "systemName": user.settings["template_settings"]["system_name"],
            "channel": "F",
            "epkId": user.message.payload["epkId"],
            "mode": self.mode,
        }
        items = {
            "params": {
                "url": "http://localhost:8088/api/v1/search/epkId",
                "method": "post",
                "json": command_params,
                "headers": {
                  "Content-Type": "application/json"
                }
            },
            "store": "rtdm_get_response",
            "behavior": "common_behavior"
        }
        return HTTPRequestAction(items).run(user, text_preprocessing_result, params)
