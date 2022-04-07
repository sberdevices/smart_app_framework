# coding=utf-8
from typing import Iterable
from lazy import lazy
import json
import uuid

from core.configs.global_constants import CALLBACK_ID_HEADER
from core.message.app_info import AppInfo
from core.message.device import Device
from core.names import field
import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.utils.masking_message import masking
from core.utils.pickle_copy import pickle_deepcopy
from core.utils.utils import current_time_ms
from core.message.msg_validator import MessageValidator


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
    MESSAGE_NAME = "messageName"
    MESSAGE_ID = "messageId"
    UUID = "uuid"
    PAYLOAD = "payload"
    SESSION_ID = "sessionId"
    CALLBACK_ID_HEADER_NAME = CALLBACK_ID_HEADER

    incremental_id: str
    message_name: str
    payload: dict
    uuid: dict

    def __init__(self, value: str, topic_key: str = None, creation_time=None, kafka_key: str = None, headers=None,
                 masking_fields=None, headers_required=True, validators: Iterable[MessageValidator] = ()):
        self.logging_uuid = str(uuid.uuid4())
        self._value = value
        self._as_dict = json.loads(self.value)
        self.topic_key = topic_key
        self.kafka_key = kafka_key
        self.creation_time = creation_time or current_time_ms()
        self._headers_required = headers_required
        if self._headers_required and headers is None:
            raise LookupError(f"{self.__class__.__name__} no incoming headers.")
        self.headers = Headers(headers)
        self._callback_id = None  # FIXME: by some reason it possibly to change callback_id
        self.masking_fields = masking_fields
        self.validators = validators

    def validate(self):
        """
            Try to json.load message and check for all required fields
        """

        for validator in self.validators:
            if not validator.validate(self.message_name, self.payload):
                return False

        if self._headers_required and not self.headers:
            log("Message headers is empty", level="ERROR")
            return False

        try:
            for r_field in self._required_fields:
                if r_field not in self.as_dict:
                    self.print_validation_error(r_field)
                    return False

                if r_field not in self.__annotations__:
                    continue

                if not isinstance(
                        self.as_dict[r_field],
                        self.__annotations__[r_field],
                ):
                    self.print_validation_error(
                        r_field,
                        self.__annotations__[r_field],
                    )
                    return False

        except (json.JSONDecodeError, TypeError):
            log(
                "Message validation error: json decode error",
                exc_info=True,
                level="ERROR",
            )
            self.print_validation_error()
            return False

        return True

    def print_validation_error(
            self,
            required_field=None,
            required_field_type=None,
    ):
        if self._value:
            params = {
                "value": str(self._value),
                "required_field": required_field,
                "required_field_type": required_field_type,
                log_const.KEY_NAME: log_const.EXCEPTION_VALUE
            }
            if required_field and required_field_type:
                log(
                    "Message validation error: Expected '%(required_field)s'"
                    " of type '%(required_field_type)s': %(value)s",
                    params=params,
                    level="ERROR",
                )
            elif required_field:
                log(
                    "Message validation error: Required field "
                    "'%(required_field)s' is missing: %(value)s",
                    params=params,
                    level="ERROR",
                )
            else:
                log(
                    "Message validation error: Format is wrong: %(value)s",
                    params=params,
                    level="ERROR",
                )
        else:
            log("Message validation error: Message is empty", level="ERROR")

    @property
    def _callback_id_header_name(self):
        return CALLBACK_ID_HEADER

    @property
    def _required_fields(self):
        return {self.MESSAGE_ID, self.UUID, self.PAYLOAD, self.SESSION_ID, self.MESSAGE_NAME}

    @property
    def session_id(self):
        return self.as_dict.get(self.SESSION_ID)

    # database user_id
    @property
    def db_uid(self):
        return "{}_{}_{}".format(self.sub, self.uid, self.channel)

    @property
    def channel(self):
        return self.uuid.get(field.USER_CHANNEL)

    @property
    def uid(self):
        return self.uuid.get(field.USER_ID)

    @property
    def sub(self):
        return self.uuid.get(field.SUB)

    @property
    def uuid(self):
        return self.as_dict[self.UUID]

    @property
    def payload(self):
        return self.as_dict[self.PAYLOAD]


    @property
    def type(self):
        return self.as_dict[self.MESSAGE_NAME]

    def project_name(self):
        return self.payload.get(field.PROJECT_NAME)

    @property
    def intent(self):
        return self.payload.get(field.INTENT)

    @property
    def device(self):
        return Device(self.payload.get(field.DEVICE) or {})

    @property
    def app_info(self):
        return AppInfo(self.payload.get(field.APP_INFO) or {})

    @property
    def smart_bio(self):
        return self.payload.get(field.SMART_BIO) or {}

    @property
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

    @property
    def has_callback_id(self):
        return self._callback_id is not None or self.headers.get(self._callback_id_header_name) is not None

    # noinspection PyMethodMayBeStatic
    def generate_new_callback_id(self):
        return str(uuid.uuid4())

    @property
    def masked_value(self):
        data = pickle_deepcopy(self.as_dict)
        masking(data, self.masking_fields)
        return json.dumps(data, ensure_ascii=False)

    @property
    def message_name(self):
        return self.as_dict[self.MESSAGE_NAME]

    # unique message_id
    @property
    def incremental_id(self):
        return self.as_dict[self.MESSAGE_ID]

    @property
    def as_dict(self):
        return self._as_dict

    @property
    def value(self):
        return self._value

basic_error_message = SmartAppFromMessage(
    '''
    {
        "messageName": "ERROR",
        "messageId": -1,
        "uuid": -1,
        "payload": {},
        "sessionId": -1
    }
    ''',
    headers={},
    headers_required=False,
)
