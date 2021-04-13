import json
import logging
import types

import requests

from smart_kit.text_preprocessing.http_text_normalizer import NormalizationError


def to_bool(value):
    if str(value).lower() == "true":
        return True

    if str(value).lower() == "false":
        return False

    if str(value).isdigit():
        value = int(value)

    return bool(value)


def as_is(value):
    return value


__typecast_map = {
    bool: to_bool,
    float: float,
    int: int,
    str: str,
}

TYPECAST_MAP = types.MappingProxyType(__typecast_map)


class TypeCastByAnnotation:
    # Чет выглядит ваще как техномагия
    def items(self):
        res = []
        for var_name in self:
            res.append((var_name, getattr(self, var_name)))
        return res

    def __setattr__(self, key: str, value):
        if key in self.__annotations__:
            _type = self.__annotations__[key]
            _type = TYPECAST_MAP.get(_type, as_is)
        else:
            _type = as_is
        value = _type(value)

        return super().__setattr__(key, value)

    def __contains__(self, item):
        return item in self.__vars__()

    def __iter__(self):
        return iter(self.__vars__())

    def __vars__(self):
        _vars = [
            k for k in self.__dir__()
            if k[:2] != '__' and type(getattr(self, k, '')).__name__ != 'method'
        ]
        return [
            var
            for var in _vars
            if not (var.startswith("_") or var == "exclude" or var in self.exclude)
        ]

    exclude = ()


class Environment(TypeCastByAnnotation):
    chat_id: str
    device_capabilities_misc: bool
    device_capabilities_screen: bool
    device_capabilities_speak: bool
    device_channel: str
    device_channel_version: str
    device_client_type: str
    device_platform_name: str
    device_platform_version: str
    device_surface_version: str
    intent: str
    message_id: int
    message_name: str
    meta_time_timestamp: int
    meta_time_timezone_id: str
    meta_time_timezone_offset_sec: int
    new_session: bool
    project_name: str
    user_channel: str
    user_id: str

    exclude = ("as_dict",)

    def __init__(self):
        from smart_kit.configs import get_app_config

        self.__message = {"original_text": ""}
        self.character_appeal = "official"
        self.character_gender = "male"
        self.character_id = "sber"
        self.character_name = "Сбер"
        self.chat_id = "1"
        self.config = get_app_config()
        self.device_capabilities_misc = True
        self.device_capabilities_screen = True
        self.device_capabilities_speak = True
        self.device_channel = "MP_SBOL_IOS"
        self.device_channel_version = "9.1"
        self.device_client_type = "RETAIL"
        self.device_platform_name = "iPhone"
        self.device_platform_type = "IOS"
        self.device_platform_version = "11.1"
        self.device_surface = "SBOL"
        self.device_surface_version = "testSurfaceVersion"
        self.intent = None
        self.message_id = 0
        self.message_name = "MESSAGE_TO_SKILL"
        self.meta_time_timestamp = 1432233446145000
        self.meta_time_timezone_id = "Europe/Moscow"
        self.meta_time_timezone_offset_sec = 10800
        self.new_session = False
        self.project_name = "test_project_name"
        self.user_channel = None
        self.user_id = "local_testing_1"

    @property
    def as_dict(self):
        return {
            "messageId": self.message_id,
            "messageName": self.message_name,
            "uuid": {
                "userChannel": self.user_channel,
                "chatId": self.chat_id,
                "userId": self.user_id,
            },
            "payload": {
                "character": {
                    "id": self.character_id,
                    "name": self.character_name,
                    "gender": self.character_gender,
                    "appeal": self.character_appeal,
                },
                "device": {
                    "platformType": self.device_platform_type,
                    "platformVersion": self.device_platform_version,
                    "surface": self.device_surface,
                    "surfaceVersion": self.device_surface_version,
                    "features": {
                        "appTypes": ["DIALOG", "WEB_APP"],
                    },
                    "capabilities": {
                        "misc": {
                            "available": self.device_capabilities_misc,
                        },
                        "screen": {
                            "available": self.device_capabilities_screen,
                        },
                        "speak": {
                            "available": self.device_capabilities_speak,
                        },
                    },
                },
                "intent": self.intent,
                "message": self.__message,
                "meta": {
                    "time": {
                        "timezone_id": self.meta_time_timezone_id,
                        "timezone_offset_sec": self.meta_time_timezone_offset_sec,
                        "timestamp": self.meta_time_timestamp,
                    },
                },
                "new_session": self.new_session,
                "personInfo": {},
                "projectName": self.project_name,
            },
        }

    @property
    def text(self):
        return self.__message["original_text"]

    @text.setter
    def text(self, value):
        from smart_kit.configs import get_app_config
        config = get_app_config()

        try:
            recognizer = config.NORMALIZER
            norm = recognizer(value)
            tpr = {'original_text': norm['original_text'],
                   'normalized_text': norm['normalized_text'],
                   'tokenized_elements_list': norm['tokenized_elements_list']}
        except (requests.exceptions.RequestException, NormalizationError) as exc:
            tpr = {"original_text": value}
            logging.getLogger(__file__).warning(
                f"\nError due connection to Text Normalizer Server at {self.config.NORMALIZER_ADDRESS}.\n"
                f"Result replaced with empty dict.\n"
                f"You see this warning because you have enabled debug mode at app_config.py.\n"
                f"Error: {exc}"
            )

        self.__message = tpr

    def __str__(self):
        return json.dumps(self.as_dict)


class Settings(TypeCastByAnnotation):
    DISPLAY_RAW: bool = False

