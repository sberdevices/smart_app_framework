import cmd
import json
import os
import pprint
import typing

from lazy import lazy

from core.descriptions.descriptions import Descriptions
from core.message.from_message import SmartAppFromMessage
from smart_kit.compatibility.commands import combine_commands
from smart_kit.testing import suite
from smart_kit.testing import utils


class CLInterface(cmd.Cmd):
    intro = "Привет!\t Введите help или ? для вызова списка команд.\n"
    prompt = "> "
    VPS_KEYS = ["answer", "pronounceText", "items", "suggestions"]

    def __init__(
            self, configs_path, secret_path, settings_cls, references_path,
            resources_cls, model_cls, test_case_cls, dialogue_manager_cls, user_cls, parametrizer_cls,
            from_msg_cls, app_name,
    ):
        super().__init__()
        self.configs_path = configs_path
        self.references_path = references_path
        self.settings = settings_cls(config_path=self.configs_path, secret_path=secret_path,
                                     references_path=self.references_path)

        self.environment = utils.Environment()
        self.lt_settings = utils.Settings()

        self.user_data = None

        self.__resources_cls = resources_cls
        self.__model_cls = model_cls
        self.__dialogue_manager_cls = dialogue_manager_cls
        self.__user_cls = user_cls
        self.__parametrizer_cls = parametrizer_cls
        self.__from_msg_cls = from_msg_cls
        self.__test_case_cls = test_case_cls

        predefined_fields_storage_path = os.path.join(self.references_path, "./predefined_fields_storage.json")
        if os.path.exists(predefined_fields_storage_path):
            with open(str(predefined_fields_storage_path), "r") as f:
                self.storaged_predefined_fields = json.load(f)
        else:
            self.storaged_predefined_fields = {}

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
        if ans["messageName"] == "ANSWER_TO_USER":
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

    def do_run(self, file_name: str):
        try:
            suite.run_testfile(
                os.getcwd(),
                file_name,
                self.app_model,
                self.settings,
                self.__user_cls,
                self.__parametrizer_cls,
                self.__from_msg_cls,
                self.__test_case_cls,
                self.storaged_predefined_fields,
                interactive=True,
            )
        except FileNotFoundError:
            print("Нужно указать относительный путь до json файла.")

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
        from smart_kit.configs import get_app_config
        masking_fields = self.settings["template_settings"].get("masking_fields")
        message = SmartAppFromMessage(raw_message, headers=headers, masking_fields=masking_fields,
                                      validators=get_app_config().FROM_MSG_VALIDATORS)
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
            ans = answer.raw
            print("{}\nrequest type: {}\n".format(self.format_answer_value(ans), answer.request_type))
            if ans["messageName"] == "ANSWER_TO_USER":
                params = ans["payload"]
                intent = params.get("intent")
                if intent:
                    self.environment.intent = intent
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
