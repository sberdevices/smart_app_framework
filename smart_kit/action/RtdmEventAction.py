# coding: utf-8
import datetime
import json
import requests
from uuid import uuid4
from typing import Union, Dict, List, Any, Optional

from core.basic_models.actions.basic_actions import CommandAction
from core.basic_models.actions.command import Command
from core.text_preprocessing.base import BaseTextPreprocessingResult
from scenarios.user.user_model import User


class RtdmGetPpAndEventsAction(CommandAction):
    """
    Action получения ПП и событий из RTDM. Полученные данные сохраняются в user-переменную
    rtdm_get_pp_and_events_response.

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
        self.channel: str = items["channel"]
        self.mode: str = items["mode"]
        self.epkId: str = items["epkId"]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
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
        user.variables.set("rtdm_get_pp_and_events_response", pull_api_service_response_dict)
        return []


class RtdmEventAction(CommandAction):
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
            "messageId": user.message.as_dict[user.message.MESSAGE_ID],
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
