import json
import os
from csv import DictWriter, QUOTE_MINIMAL
from typing import AnyStr, Optional, Tuple, Any, Dict, Callable

from lazy import lazy

from core.configs.global_constants import LINK_BEHAVIOR_FLAG
from smart_kit.compatibility.commands import combine_commands
from smart_kit.configs import Settings
from smart_kit.message.smartapp_to_message import SmartAppToMessage
from smart_kit.models.smartapp_model import SmartAppModel
from smart_kit.request.kafka_request import SmartKitKafkaRequest
from smart_kit.testing.utils import Environment
from smart_kit.utils.diff import partial_diff


def run_testfile(path: AnyStr, file: AnyStr, app_model: SmartAppModel, settings: Settings, user_cls: type,
                 parametrizer_cls: type, from_msg_cls: type, test_case_cls: type, storaged_predefined_fields: Dict[str, Any],
                 csv_file_callback: Optional[Callable[[str], Callable[[Any], None]]],
                 interactive: bool = False) -> Tuple[int, int]:
    test_file_path = os.path.join(path, file)
    if not os.path.isfile(test_file_path) or not test_file_path.endswith('.json'):
        raise FileNotFoundError
    with open(test_file_path, "r") as test_file:
        json_obj = json.load(test_file)
    success = 0
    for test_case in json_obj:
        test_params = json_obj[test_case]
        if isinstance(test_params, list):
            test_params = {"messages": test_params, "user": {}}
        print(f"[+] Processing test case {test_case} from {test_file_path}")
        if csv_file_callback:
            csv_case_callback = csv_file_callback(test_case)
        else:
            csv_case_callback = None
        if test_case_cls(
                app_model,
                settings,
                user_cls,
                parametrizer_cls,
                from_msg_cls,
                **test_params,
                storaged_predefined_fields=storaged_predefined_fields,
                interactive=interactive,
                csv_case_callback=csv_case_callback,
        ).run():
            print(f"[+] {test_case} OK")
            success += 1
    print(f"[+] {file} {success}/{len(json_obj)}")
    return len(json_obj), success


class TestSuite:
    def __init__(self, path: AnyStr, app_config: Any, predefined_fields_storage: AnyStr, make_csv: bool):
        self.path = path
        self.app_config = app_config

        self.csv_callback = None
        if make_csv:
            field_names = ['file', 'test_case', 'success', 'diff']
            results_csv_writer = DictWriter(
                open(os.path.join(path, f'tests_results.csv'), 'wt'),
                fieldnames=field_names,
                quoting=QUOTE_MINIMAL
            )
            results_csv_writer.writeheader()

            def __csv_file_callback(file):
                def __csv_test_case_callback(test_case_name):
                    def __write_csv_line(diff):
                        results_csv_writer.writerow(dict(zip(
                            field_names,
                            [file, test_case_name, 0 if diff else 1, diff.serialize()]
                        )))
                    return __write_csv_line
                return __csv_test_case_callback
            self.csv_callback = __csv_file_callback

        with open(predefined_fields_storage, "r") as f:
            self.storaged_predefined_fields = json.load(f)

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
                if self.csv_callback:
                    csv_file_callback = self.csv_callback(file)
                else:
                    csv_file_callback = None
                file_total, file_success = run_testfile(
                    path,
                    file,
                    self.app_model,
                    self.settings,
                    self.app_config.USER,
                    self.app_config.PARAMETRIZER,
                    self.app_config.FROM_MSG,
                    self.app_config.TEST_CASE,
                    self.storaged_predefined_fields,
                    csv_file_callback
                )
                total += file_total
                total_success += file_success

        print(f"[+] Total: {total_success}/{total}")


class TestCase:
    def __init__(self, app_model: SmartAppModel, settings: Settings, user_cls: type, parametrizer_cls: type,
                 from_msg_cls: type, messages: dict, storaged_predefined_fields: Dict[str, Any], interactive: bool,
                 csv_case_callback: Optional[Callable[[Any], None]] = None, user: Optional[dict] = None):
        self.messages = messages
        self.user_state = json.dumps(user)
        self.interactive = interactive

        self.app_model = app_model
        self.settings = settings
        self.storaged_predefined_fields = storaged_predefined_fields
        self.csv_case_callback = csv_case_callback

        self.__parametrizer_cls = parametrizer_cls
        self.__user_cls = user_cls
        self.__from_msg_cls = from_msg_cls

    def run(self) -> bool:
        success = True

        app_callback_id = None
        for index, message_ in enumerate(self.messages):
            print('Шаг', index)
            if index and self.interactive:
                print("Нажмите ENTER, чтобы продолжить...")
                input()

            request = message_["request"]
            response = message_["response"]

            # Если использован флаг linkPreviousByCallbackId и после предыдущего сообщения был сохранен app_callback_id,
            # сообщению добавляются заголовки. Таким образом, сработает behavior, созданный предыдущим запросом
            if message_.get(LINK_BEHAVIOR_FLAG) and app_callback_id:
                headers = [(self.__from_msg_cls.CALLBACK_ID_HEADER_NAME, app_callback_id.encode())]
            else:
                headers = [('kafka_correlationId', 'test_123')]
            message = self.create_message(request, headers=headers)

            user = self.__user_cls(
                id=message.uid, message=message, db_data=self.user_state, settings=self.settings,
                descriptions=self.app_model.scenario_descriptions,
                parametrizer_cls=self.__parametrizer_cls
            )

            self.post_setup_user(user)

            commands = self.app_model.answer(message, user) or []

            answers = self._generate_answers(
                user=user, commands=commands, message=message
            )

            predefined_fields_resp = response.get("predefined_fields")
            if predefined_fields_resp:
                response = self.handle_predefined_fields_response(predefined_fields_resp, response)
            expected_answers = response["messages"]
            expected_user = response["user"]

            if len(commands) != len(response["messages"]):
                print(
                    f"[!] Expected quantity of messages differ from received.\n"
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
                if self.csv_case_callback:
                    self.csv_case_callback(diff)
                # Последний app_callback_id в answers, используется в заголовках следующего сообщения
                app_callback_id = actual.request.values.get(self.__from_msg_cls.CALLBACK_ID_HEADER_NAME, app_callback_id)

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

    def create_message(self, data, headers=None):
        defaults = Environment().as_dict

        predefined_fields = data.get("predefined_fields")
        is_payload_field = data.get("payload")
        if predefined_fields:
            predefined_fields_data = self.storaged_predefined_fields[predefined_fields]
            if not is_payload_field and not predefined_fields_data.get("payload"):
                predefined_fields_data = {"payload": predefined_fields_data}
            if is_payload_field and predefined_fields_data.get("payload"):
                raise Exception("Payload field is in test case and in predefined_fields object, check it!")
            defaults.update(predefined_fields_data)
            del data["predefined_fields"]

        message = data.get("message")
        if message:
            defaults["payload"].update({"message": message})

        defaults.update(data)
        return self.__from_msg_cls(json.dumps(defaults), headers=headers)

    def handle_predefined_fields_response(self, predefined_fields_resp, response):
        predefined_fields_resp_data = self.storaged_predefined_fields[predefined_fields_resp]
        response.update(predefined_fields_resp_data)
        del response["predefined_fields"]

        pronounce_texts = response.get("pronounce_texts", [])
        if pronounce_texts:
            for text, msg_dict in zip(pronounce_texts, response["messages"]):
                msg_dict["payload"]["pronounceText"] = text
            del response["pronounce_texts"]

        return response

    def post_setup_user(self, user):
        pass
