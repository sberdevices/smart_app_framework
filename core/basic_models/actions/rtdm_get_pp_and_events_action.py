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
    Action получения ПП и событий из RTDM. Полученные данные сохраняются в user-переменную
    rtdm_get_response.

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
        self.mode: str = items["mode"]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        command_params = {
            "rqUid": user.message.incremental_id,
            "rqTm": datetime.datetime.now().replace(microsecond=0).isoformat(),
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
