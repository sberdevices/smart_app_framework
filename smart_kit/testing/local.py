import cmd
import logging
import pprint
import typing

import requests
import json
from core.descriptions.descriptions import Descriptions
from core.message.from_message import SmartAppFromMessage
from lazy import lazy

from smart_kit.compatibility.commands import combine_commands
from smart_kit.testing import type_casting
from smart_kit.text_preprocessing.http_text_normalizer import NormalizationError


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
            _type = type_casting.TYPECAST_MAP.get(_type, type_casting.as_is)
        else:
            _type = type_casting.as_is
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
    intent: str
    user_id: str
    chat_id: str
    message_id: int
    device_channel: str
    device_channel_version: str
    device_client_type: str
    device_platform_name: str
    device_platform_version: str
    csa_profile_id: int
    message_name: str
    token: str
    project_name: str
    new_session: bool
    user_channel: str

    exclude = ("as_dict",)

    def __init__(self):
        self.intent = None
        self.user_id = "local_testing_1"
        self.chat_id = "1"
        self.message_id = 0
        self.device_channel = "MP_SBOL_IOS"
        self.device_channel_version = "9.1"
        self.device_client_type = "RETAIL"
        self.device_platform_name = "iPhone"
        self.device_platform_version = "11.1"
        self.csa_profile_id = 123
        self.message_name = "MESSAGE_TO_SKILL"

        self.token = "test_token"
        self.project_name = "test_project_name"

        self.user_channel = None

        self.__message = {
            "original_text": ""
        }

        self.new_session = False
        from smart_kit.configs import get_app_config
        self.config = get_app_config()

    @property
    def as_dict(self):
        return {
            "messageId": self.message_id,
            "messageName": self.message_name,
            "uuid": {
                "userChannel": self.user_channel,
                "chatId": self.chat_id,
                "userId": self.user_id
            },
            "payload": {
                "personInfo": {},
                "device": {"client_type": self.device_client_type, "channel": self.device_channel,
                           "channel_version": self.device_channel_version,
                           "platform_name": self.device_platform_name,
                           "platform_version": self.device_platform_version},
                "projectName": self.project_name,
                "intent": self.intent,
                "token": self.token,
                "new_session": self.new_session,
                "message": self.__message
            }
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


class CLInterface(cmd.Cmd):
    intro = "Привет!\t Введите help или ? для вызова списка команд.\n"
    prompt = "> "
    VPS_KEYS = ["answer", "pronounceText", "items", "suggestions"]

    def __init__(
            self, configs_path, secret_path, settings_cls, references_path,
            resources_cls, model_cls, dialogue_manager_cls, user_cls, parametrizer_cls,
            app_name,
    ):
        super().__init__()
        self.configs_path = configs_path
        self.references_path = references_path
        self.settings = settings_cls(config_path=self.configs_path, secret_path=secret_path,
                                     references_path=self.references_path)

        self.environment = Environment()
        self.lt_settings = Settings()

        self.user_data = None

        self.__resources_cls = resources_cls
        self.__model_cls = model_cls
        self.__dialogue_manager_cls = dialogue_manager_cls
        self.__user_cls = user_cls
        self.__parametrizer_cls = parametrizer_cls

    def after_process_message(self, message) -> typing.Optional[str]:
        callback = getattr(self, f"on_{message.name.lower()}", lambda *args, **kwargs: None)
        return callback(message)

    @lazy
    def app_model(self):
        return self.__model_cls(self.resources, self.__dialogue_manager_cls, custom_settings=self.settings)

    @lazy
    def resources(self):
        source = self.settings.get_source()

        return self.__resources_cls(source, self.references_path, self.settings)

    @lazy
    def available_scenarios(self):
        return list(Descriptions(self.resources.registered_repositories)["scenarios"].keys())

    @staticmethod
    def format_answer_value(ans):
        resp = ""
        if ans["message_name"] == "ANSWER_TO_USER":
            params = ans["payload"]
            for k in CLInterface.VPS_KEYS:
                if params.get(k):
                    resp += "{}: {}\n".format(k, params[k])
            if not resp:
                resp += "answer: <пустой ответ>\n"
            for key in filter(lambda key: key not in CLInterface.VPS_KEYS, params.keys()):
                if isinstance(params[key], list):
                    resp += "\t" + " | ".join("[{:^40}]".format(item) for item in params[key]) + "\n"
                else:
                    resp += "Other node {}:\t{}\n".format(key, params[key])
        else:
            resp += json.dumps(ans)
        return resp.strip()

    def do_show_envs(self, _input: str):
        self._show_envs()

    def do_set(self, _input: str):
        try:
            var, value = _input.split(' ', maxsplit=1)
        except ValueError:
            print("Нужно указать переменную и значение. Недостаточно данных")
            self._show_envs()
            return

        if var in self.environment:
            setattr(self.environment, var, value)
        elif var in self.lt_settings:
            setattr(self.lt_settings, var, value)
        else:
            print(f"Неизвестное значение: {var}")
            return

        print(f"{var} = {value}")

    def complete_set(self, text, line, begidx, endidx):
        names = list(self.environment) + list(self.lt_settings)
        return list(filter(lambda t: t.startswith(text), names))

    def do_show_scenarios(self, _input: str):
        for scen_name in self.available_scenarios:
            print(f"\t{scen_name}")

    def preloop(self):
        if len(self.available_scenarios) == 0:
            print("Нет доступных сценариев.")
            exit(0)

        self.environment.intent = self.available_scenarios[0]
        print("Текущий сценарий: ", self.environment.intent)

    def process_message(self, raw_message: str, headers: tuple = ()) -> typing.Tuple[typing.Any, list]:
        masking_fields = self.settings["template_settings"].get("masking_fields")
        message = SmartAppFromMessage(raw_message, headers=headers, masking_fields=masking_fields)
        user = self.__user_cls(self.environment.user_id, message, self.user_data, self.settings,
                               self.app_model.scenario_descriptions,
                               self.__parametrizer_cls, load_error=False)
        answers = self.app_model.answer(message, user)
        return user, answers or []

    def default(self, _input: str):
        self.environment.text = _input
        self.environment.message_id += 1

        if self.lt_settings.DISPLAY_RAW:
            pprint.pprint(self.environment.as_dict)

        user, answers = self.process_message(str(self.environment))
        self.user_data = user.raw_str

        answers = combine_commands(answers, user)
        for answer in answers:
            respond = self.after_process_message(answer)
            if respond:
                _, new_answers = self.process_message(
                    respond,
                    (('app_callback_id', answer.request_data['app_callback_id'].encode()),),
                )
                answers.extend(new_answers or [])

        if not answers:
            print("Нет ответа")
            return

        for answer in answers:
            print("{}\nrequest type: {}\n".format(self.format_answer_value(answer.raw), answer.request_type))
            if self.lt_settings.DISPLAY_RAW:
                pprint.pprint(answer.raw)

    def run_local_testing(self):
        return self.cmdloop()

    def _show_envs(self):
        print("Доступные переменные:")
        for var_name, var_value in self.environment.items():
            print(f"\t{var_name} {var_value}")
        print("Доступные настройки:")
        for var_name, var_value in self.lt_settings.items():
            print(f"\t{var_name} {var_value}")
        # DRY!
