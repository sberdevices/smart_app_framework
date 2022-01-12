from core.model.registered import Registered
from smart_kit.message.smartapp_to_message import SmartAppToMessage

message_handlers = Registered()


def get_message_handler(command_name):
    default = SmartAppToMessage
    return message_handlers.get(command_name, default)
