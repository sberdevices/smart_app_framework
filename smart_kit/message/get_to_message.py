from core.model.registered import Registered
from smart_kit.message.smartapp_to_message import SmartAppToMessage

to_messages = Registered()


def get_to_message(command_name):
    default = SmartAppToMessage
    return to_messages.get(command_name, default)
