# coding=utf-8
from typing import Optional
from lazy import lazy
import json
import uuid

import pydantic

from core.configs.global_constants import CALLBACK_ID_HEADER
from core.message.app_info import AppInfo
from core.message.device import Device
from core.names import field
import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.utils.masking_message import masking
from core.utils.pickle_copy import pickle_deepcopy
from core.utils.utils import current_time_ms


class SmartAppPayloadModel(pydantic.BaseModel):
    intent: str
    annotations: Optional[str]


class FromMessageValueModel(pydantic.BaseModel):
    session_id: str = pydantic.Field(alias='sessionId')
    incremental_id: str = pydantic.Field(alias='messageId')
    message_name: str = pydantic.Field(alias='messageName')
    uuid: dict
    payload: dict


class Headers:
    def __init__(self, data):
        self.raw = dict(data)

    def __getitem__(self, item):
        return self.raw[item].decode()

    def get(self, key, default=None, encoding="utf-8"):
        res = self.raw.get(key)
        if res is None:
            return default
        return res.decode(encoding=encoding)

    def __bool__(self):
        return bool(self.raw)


class SmartAppFromMessage:
    VALUE_MODEL = FromMessageValueModel
    PAYLOAD_MODEL = SmartAppPayloadModel

    MESSAGE_NAME = "messageName"
    MESSAGE_ID = "messageId"
    UUID = "uuid"
    PAYLOAD = "payload"
    SESSION_ID = "sessionId"

    def __init__(
            self, value: str, topic_key: str = None,
            creation_time=None, kafka_key: str = None, headers=None,
            masking_fields=None, headers_required=True
    ):
        self.logging_uuid = str(uuid.uuid4())
        self._value = value
        self.topic_key = topic_key
        self.kafka_key = kafka_key
        self.creation_time = creation_time or current_time_ms()
        self._headers_required = headers_required
        if self._headers_required and headers is None:
            raise LookupError(f"{self.__class__.__name__} no incoming headers.")
        self.headers = Headers(headers)
        self._callback_id = None  # FIXME: by some reason it possibly to change callback_id
        self.masking_fields = masking_fields

    def validate(self):
        """
            Try to json.load message and check for all required fields
        """
        result = True

        if self._headers_required and not self.headers:
            log("Message headers is empty", level="ERROR")
            result = False

        try:
            # Validate value
            try:
                obj = self.VALUE_MODEL(**self.as_dict)
                print(obj)
                print(type(obj))
            except pydantic.ValidationError as ex:
                self.print_validation_error(ex)
                result = False

            # Validate payload
            try:
                self.PAYLOAD_MODEL(**self.payload)
            except pydantic.ValidationError as ex:
                self.print_validation_error(ex, 'payload')
                result = False

        except (json.JSONDecodeError, TypeError):
            log(
                "Message validation error: json decode error",
                exc_info=True,
                level="ERROR",
            )
            result = False

        return result

    def print_validation_error(self, ex: pydantic.ValidationError, prefix: Optional[str] = None):
        for problem in ex.errors():
            error = problem["type"].split(".")
            required_field = problem["loc"][0]
            if prefix is not None:
                required_field = f"{prefix}.{required_field}"
            required_field_type = None
            if error[0] == "type_error":
                required_field_type = error[1]
                msg = (
                    "Message validation error: Expected '%(required_field)s'"
                    " of type '%(required_field_type)s': %(value)s"
                )
            elif error[0] == "value_error" and error[1] == "missing":
                msg = (
                    "Message validation error: Required field "
                    "'%(required_field)s' is missing: %(value)s"
                )
            else:
                msg = "Message validation error: Format is wrong: %(value)s"
            params = {
                "value": str(self._value),
                "required_field": required_field,
                "required_field_type": required_field_type,
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            log(msg, params=params, level="ERROR")

    @property
    def _callback_id_header_name(self):
        return CALLBACK_ID_HEADER

    @lazy
    def session_id(self):
        return self.as_dict.get(self.SESSION_ID)

    # database user_id
    @lazy
    def db_uid(self):
        return "{}_{}_{}".format(self.sub, self.uid, self.channel)

    @lazy
    def channel(self):
        return self.uuid.get(field.USER_CHANNEL)

    @lazy
    def uid(self):
        return self.uuid.get(field.USER_ID)

    @lazy
    def sub(self):
        return self.uuid.get(field.SUB)

    @lazy
    def uuid(self):
        return self.as_dict[self.UUID]

    @lazy
    def payload(self):
        return self.as_dict[self.PAYLOAD]

    def project_name(self):
        return self.payload.get(field.PROJECT_NAME)

    @lazy
    def intent(self):
        return self.payload.get(field.INTENT)

    @lazy
    def device(self):
        return Device(self.payload.get(field.DEVICE) or {})

    @lazy
    def app_info(self):
        return AppInfo(self.payload.get(field.APP_INFO) or {})

    @lazy
    def smart_bio(self):
        return self.payload.get(field.SMART_BIO) or {}

    @lazy
    def annotations(self):
        annotations = self.payload.get(field.ANNOTATIONS) or {}
        for annotation in annotations:
            classes = annotations[annotation][field.CLASSES]
            probas = annotations[annotation][field.PROBAS]
            annotations[annotation] = dict(zip(classes, probas))
        return annotations

    @property
    def callback_id(self):
        if self._callback_id is not None:
            return self._callback_id

        try:
            return self.headers[self._callback_id_header_name]
        except KeyError:
            log(f"{self._callback_id_header_name} missed in headers for message_id %(message_id)s",
                params={log_const.KEY_NAME: "callback_id_missing", "message_id": self.incremental_id}, level="WARNING")
            return None

    @callback_id.setter
    def callback_id(self, value):
        self._callback_id = value

    # noinspection PyMethodMayBeStatic
    def generate_new_callback_id(self):
        return str(uuid.uuid4())

    @lazy
    def masked_value(self):
        data = pickle_deepcopy(self.as_dict)
        masking(data, self.masking_fields)
        return json.dumps(data, ensure_ascii=False)

    @property
    def message_name(self):
        return self.as_dict[self.MESSAGE_NAME]

    # unique message_id
    @lazy
    def incremental_id(self):
        return self.as_dict[self.MESSAGE_ID]

    @lazy
    def as_dict(self):
        return json.loads(self._value)

    @lazy
    def value(self):
        return self._value
