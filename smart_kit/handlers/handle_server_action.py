from core.names.field import SERVER_ACTION

from smart_kit.handlers.handle_respond import HandlerRespond


class HandlerServerAction(HandlerRespond):

    def get_action_name(self, payload, user):
        return payload[SERVER_ACTION]["action_id"]

    def get_action_params(self, payload):
        return payload[SERVER_ACTION].get("parameters", {})

