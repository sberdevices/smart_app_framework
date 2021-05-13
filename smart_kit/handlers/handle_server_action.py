import scenarios.logging.logger_constants as log_const

from core.names.field import SERVER_ACTION
from core.logging.logger_utils import log
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from core.utils.pickle_copy import pickle_deepcopy

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.utils.monitoring import smart_kit_metrics


class HandlerServerAction(HandlerBase):
    handler_name = "HandlerServerAction"

    def __init__(self, app_name, action_name=None, ):
        super(HandlerServerAction, self).__init__(app_name)
        self._action_name = action_name

    def get_action_name(self, payload, user):
        return payload[SERVER_ACTION]["action_id"]

    def get_action_params(self, payload):
        return payload[SERVER_ACTION].get("parameters", {})

    def run(self, payload, user):
        action_params = pickle_deepcopy(self.get_action_params(payload))
        params = {log_const.KEY_NAME: "handling_server_action",
                  "server_action_params": str(action_params),
                  "server_action_id": self.get_action_name(payload, user)}
        log("HandlerServerAction %(server_action_id)s started", user, params)

        app_info = user.message.app_info
        smart_kit_metrics.counter_incoming(self.app_name, user.message.message_name, self.__class__.__name__,
                                           user, app_info=app_info)

        action_id = self.get_action_name(payload, user)
        action = user.descriptions["external_actions"][action_id]
        return action.run(user, TextPreprocessingResult({}), action_params)
