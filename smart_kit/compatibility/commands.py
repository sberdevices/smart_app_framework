import typing

from core.basic_models.actions.command import Command
from core.names import field

from scenarios.user.user_model import User

from smart_kit.names.message_names import ANSWER_TO_USER


def combine_answer_to_user(commands: typing.List[Command]) -> Command:
    from smart_kit.configs import get_app_config
    config = get_app_config()

    answer = Command(name=ANSWER_TO_USER, request_data=commands[0].request_data, request_type=commands[0].request_type)
    summary_pronounce_text = []
    auto_listening = None
    for command in commands:
        if command.request_data != answer.request_data:
            raise ValueError(f"Cant combine {ANSWER_TO_USER} commands, request_data is different")
        if command.request_type != answer.request_type:
            raise ValueError(f"Cant combine {ANSWER_TO_USER} commands, request_type is different")

        payload = command.payload

        pronounce_text = payload.pop(field.PRONOUNCE_TEXT, None)
        items = payload.pop(field.ITEMS, None)

        if auto_listening is None:
            auto_listening = payload.get(field.AUTO_LISTENING, None)

        if pronounce_text:
            summary_pronounce_text.append(pronounce_text)

        if items is not None:
            answer.payload.setdefault(field.ITEMS, []).extend(items)

        answer.payload.update(payload)

    if summary_pronounce_text:
        answer.payload[field.PRONOUNCE_TEXT] = " ".join(summary_pronounce_text)
    answer.payload[field.AUTO_LISTENING] = auto_listening

    return answer


def combine_commands(commands: typing.List[Command], user: User, **kwargs) -> typing.List[Command]:
    user_answers = []

    for command in commands:
        if command.name == ANSWER_TO_USER:
            user_answers.append(command)

    for user_answer in user_answers:
        commands.remove(user_answer)

    if user_answers:
        answer_to_user = combine_answer_to_user(user_answers)
        last_scenario_name = user.last_scenarios.last_scenario_name
        if field.INTENT not in answer_to_user.payload:
            if last_scenario_name is not None:
                answer_to_user.payload[field.INTENT] = last_scenario_name

        debug_info = answer_to_user.payload.setdefault(field.DEBUG_INFO, {})
        debug_info[field.INTENT] = last_scenario_name
        debug_info[field.DEBUG_INFO_APP_KEY] = user.message.app_info.project_id

        if field.FINISHED not in answer_to_user.payload:
            finished = last_scenario_name is None
            answer_to_user.payload[field.FINISHED] = finished

        from smart_kit.configs import get_app_config
        config = get_app_config()
        if answer_to_user.payload.get(field.AUTO_LISTENING) is None:
            answer_to_user.payload[field.AUTO_LISTENING] = config.AUTO_LISTENING

        events = user.history.get_events()
        if events and user.history.enabled:
            history_data = dict()
            history_data[field.EVENTS] = events
            answer_to_user.payload[field.HISTORY_DATA] = history_data

        commands.append(answer_to_user)  # Order isnt important
    return commands
