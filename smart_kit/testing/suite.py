import os
import json
from lazy import lazy

from core.configs.global_constants import LINK_BEHAVIOR_FLAG, CALLBACK_ID_HEADER
from core.message.from_message import SmartAppFromMessage

from smart_kit.testing.utils import Environment
from smart_kit.utils.diff import partial_diff
from smart_kit.request.kafka_request import SmartKitKafkaRequest
from smart_kit.message.smartapp_to_message import SmartAppToMessage
from smart_kit.compatibility.commands import combine_commands


def create_message(data, headers=None):
    defaults = Environment().as_dict
    defaults.update(data)

    return SmartAppFromMessage(json.dumps(defaults), headers=headers)


def run_testfile(path, file, app_model, settings, user_cls, parametrizer_cls):
    test_file_path = os.path.join(path, file)
    if not os.path.isfile(test_file_path) or not test_file_path.endswith('.json'):
        raise FileNotFoundError
    with open(test_file_path, "r") as test_file:
        json_obj = json.load(test_file)
        success = 0
        for test_case in json_obj:
            print(f"[+] Processing test case {test_case} from {test_file_path}")
            if TestCase(
                app_model,
                settings,
                user_cls,
                parametrizer_cls,
                **json_obj[test_case],
            ).run():
                print(f"[+] {test_case} OK")
                success += 1
        print(f"[+] {file} {success}/{len(json_obj)}")
    return len(json_obj), success


class TestSuite:
    def __init__(self, path, app_config):
        self.path = path
        self.app_config = app_config

    @lazy
    def app_model(self):
        return self.app_config.MODEL(
            self.resources, self.app_config.DIALOGUE_MANAGER, custom_settings=self.settings,
            app_name=self.app_config.APP_NAME
        )

    @lazy
    def resources(self):
        source = self.settings.get_source()

        return self.app_config.RESOURCES(source, self.app_config.REFERENCES_PATH, self.settings)

    @lazy
    def settings(self):
        return self.app_config.SETTINGS(config_path=self.app_config.CONFIGS_PATH,
                                        secret_path=self.app_config.SECRET_PATH,
                                        references_path=self.app_config.REFERENCES_PATH,
                                        app_name=self.app_config.APP_NAME)

    def run(self):
        total = 0
        total_success = 0
        for path, dirs, files in os.walk(self.path):
            for file in files:
                if not file.endswith(".json"):
                    continue
                file_total, file_success = run_testfile(
                    path,
                    file,
                    self.app_model,
                    self.settings,
                    self.app_config.USER,
                    self.app_config.PARAMETRIZER,
                )
                total += file_total
                total_success += file_success

        print(f"[+] Total: {total_success}/{total}")


class TestCase:
    def __init__(self, app_model, settings, user_cls, parametrizer_cls, messages, user=None):
        self.messages = messages
        self.user_state = json.dumps(user)

        self.app_model = app_model
        self.settings = settings

        self.__parametrizer_cls = parametrizer_cls
        self.__user_cls = user_cls

    def run(self) -> bool:
        success = True

        app_callback_id = None
        for message in self.messages:

            request = message["request"]
            response = message["response"]

            # Если использован флаг linkPreviousByCallbackId и после предыдущего сообщения был сохранен app_callback_id,
            # сообщению добавляются заголовки. Таким образом, сработает behavior, созданный предыдущим запросом
            if message.get(LINK_BEHAVIOR_FLAG) and app_callback_id:
                headers = [(CALLBACK_ID_HEADER, app_callback_id.encode())]
            else:
                headers = [('kafka_correlationId', 'test_123')]
            message = create_message(request, headers=headers)

            user = self.__user_cls(
                id=message.uid, message=message, db_data=self.user_state, settings=self.settings,
                descriptions=self.app_model.scenario_descriptions,
                parametrizer_cls=self.__parametrizer_cls
            )

            commands = self.app_model.answer(message, user) or []

            answers = self._generate_answers(
                user=user, commands=commands, message=message
            )
            expected_answers = response["messages"]
            expected_user = response["user"]

            if len(commands) != len(response["messages"]):
                print(
                    f"[!] Expected quantity of mesages differ from received.\n"
                    f" Expected: {len(response['messages'])}. Actual: {len(answers)}."
                )
                success = False
                continue

            app_callback_id = None
            for actual, expected in zip(answers, expected_answers):
                actual_value = actual.as_dict
                diff = partial_diff(expected, actual_value)
                if diff:
                    success = False
                    print(diff)
                # Последний app_callback_id в answers, испольуется в заголовках следующего сообщения
                app_callback_id = actual.request.values.get(CALLBACK_ID_HEADER, app_callback_id)

            user_diff = partial_diff(expected_user, user.raw)
            if user_diff:
                success = False
                print(user_diff)
            self.user_state = user.raw_str
        return success

    def _generate_answers(self, user, commands, message):
        answers = []
        commands = commands or []

        commands = combine_commands(commands, user)

        for command in commands:
            request = SmartKitKafkaRequest(id=None, items=command.request_data)
            answer = SmartAppToMessage(command=command, message=message, request=request)
            answers.append(answer)
        return answers
