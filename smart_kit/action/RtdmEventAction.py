# coding: utf-8
import datetime
import json
from requests import Response
from copy import copy
from uuid import uuid4
from typing import Union, Dict, List, Any, Optional

import requests
from core.basic_models.actions.basic_actions import CommandAction
from core.basic_models.actions.command import Command
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate
from scenarios.user.user_model import User
from lazy import lazy

from smart_kit.message.smartapp_to_message import SmartAppToMessage


class RtdmEventAction(CommandAction):
    """
    Action получения ПП и событий из RTDM

    Пример отправляемого запроса:
    {
        "rqUid":"5c975471-ecb1-4301-b1ee-a8ddb9de0c3a",
        "rqTm":"20-08-2020T14:05:00",
        "systemName":"nlpSystem",
        "channel":"F",
        "epkId":34234608109,
        "mode":"offerParam,serviceParam"
    }
    Пример ответа:
    {
       "rqUid":"5a999111-eeb1-0001-b1ee-a7ddd9de0c3a",
       "rqTm":"2021-03-04T10:05:00",
       "systemName":"nlpsystem",
       "channel":"F",
       "epkId":"00000000001",
       "offers":[
          {
             "notificationId":"23661232134301",
             "type":"OFFER_BATCH",
             "campaignId":"BC777ABD00",
             "offerKind":"E0110001",
             "priority":1,
             "data":{
                "notificationCode":"Potreb_Credit",
                "V7":"12",
                "V6":"200001",
                "V10":"60",
                "V11":"5340"
             }
          },
          {
             "notificationId":"CMT426111",
             "type":"OFFER_BATCH",
             "campaignId":"BC111ABD66",
             "offerKind":"E0330003",
             "priority":1,
             "data":{
                "notificationCode":"Deposit",
                "V17":"Дополнительный процент",
                "V18":"100 000 ₽",
                "V19":"cрок (3, 6 или 12 месяцев)",
                "V21":"android-app://ru.sberbankmobile/android-app/ru.sberbankmobile/products/deposit?action=create",
                "V20":"sberbankonline://payments/new-deposit?depositType=92&depositGroup=4"
             }
          }
       ],
       "service":[
          {
             "notificationId":"23661232134301",
             "type":"SERVICE_EVENT",
             "campaignId":"BC777ABD00",
             "priority":1,
             "data":{
                "notificationCode":"003",
                "date":1596786406000,
                "amount":1000,
                "currency":"руб",
                "transactionType":6538,
                "transactionRespCode":822,
                "atmNumber":"961072",
                "bin":220056,
                "cardMask":5522
             }
          }
       ],
       "status":{
          "code":0,
          "message":"Успешно"
       }
    }
    """

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
            "rqUid": uuid4(),
            "rqTm": datetime.datetime.now().replace(microsecond=0).isoformat(),
            "systemName": user.settings["template_settings"]["system_name"],
            "channel": self.channel,
            "epkId": self.epkId,
            "mode": self.mode
        }
        pull_api_service_response = requests.post("http://localhost:8088/api/v1/search/epkId",
                                                  json.dumps(command_params))
        pull_api_service_response_dict = json.loads(pull_api_service_response.text)
        # Отправка отклика клиента по ПП
        commands = [Command(self.command, pull_api_service_response_dict, self.id, request_type=self.request_type,
                            request_data=self.request_data)]
        return commands


class RtdmEventAction(CommandAction):
    """
    Action получения ПП и событий из RTDM

    Пример::

        {
            "type": "rtdm_info_event_action",
            "notification_id": "{{ rtdm.offers[0].notificationId }}",
            "feedback_status": "FS",
            "description": "Вклад ВА ПП"
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

        pull_api_service_response = requests.post("http://localhost:8088/api/v1/search/epkId",
                                                  json.dumps(command_params))
        pull_api_service_response_dict = json.loads(pull_api_service_response.text)
        # Отправка отклика клиента по ПП
        commands = [Command(self.command, pull_api_service_response_dict, self.id, request_type=self.request_type,
                            request_data=self.request_data)]
        return commands


class SmartAppRtdmToMessage(SmartAppToMessage):

    @lazy
    def as_dict(self):
        return self.payload


a = {
"rqUid":"5c975471-ecb1-4301-b1ee-a8ddb9de0c3a",
"rqTm":"20-08-2020T14:05:00",
"systemName":"nlpSystem",
"channel":"F",
"epkId":34234608109,
"mode":"offerParam,serviceParam"
}
b = {
   "rqUid":"5a999111-eeb1-0001-b1ee-a7ddd9de0c3a",
   "rqTm":"2021-03-04T10:05:00",
   "systemName":"nlpsystem",
   "channel":"F",
   "epkId":"00000000001",
   "offers":[
      {
         "notificationId":"23661232134301",
         "type":"OFFER_BATCH",
         "campaignId":"BC777ABD00",
         "offerKind":"E0110001",
         "priority":1,
         "data":{
            "notificationCode":"Potreb_Credit",
            "V7":"12",
            "V6":"200001",
            "V10":"60",
            "V11":"5340"
         }
      },
      {
         "notificationId":"CMT426111",
         "type":"OFFER_BATCH",
         "campaignId":"BC111ABD66",
         "offerKind":"E0330003",
         "priority":1,
         "data":{
            "notificationCode":"Deposit",
            "V17":"Дополнительный процент",
            "V18":"100 000 ₽",
            "V19":"cрок (3, 6 или 12 месяцев)",
            "V21":"android-app://ru.sberbankmobile/android-app/ru.sberbankmobile/products/deposit?action=create",
            "V20":"sberbankonline://payments/new-deposit?depositType=92&depositGroup=4"
         }
      }
   ],
   "service":[
      {
         "notificationId":"23661232134301",
         "type":"SERVICE_EVENT",
         "campaignId":"BC777ABD00",
         "priority":1,
         "data":{
            "notificationCode":"003",
            "date":1596786406000,
            "amount":1000,
            "currency":"руб",
            "transactionType":6538,
            "transactionRespCode":822,
            "atmNumber":"961072",
            "bin":220056,
            "cardMask":5522
         }
      }
   ],
   "status":{
      "code":0,
      "message":"Успешно"
   }
}
b = {
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
