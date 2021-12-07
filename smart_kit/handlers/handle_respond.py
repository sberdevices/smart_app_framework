from time import time

from core.logging.logger_utils import log

from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
import scenarios.logging.logger_constants as log_const

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.names.action_params_names import TO_MESSAGE_NAME, SEND_TIMESTAMP
from smart_kit.utils.monitoring import smart_kit_metrics


class HandlerRespond(HandlerBase):
    handler_name = "HandlerRespond"

    def __init__(self, app_name, action_name=None, ):
        super(HandlerRespond, self).__init__(app_name)
        self._action_name = action_name

    def get_action_name(self, payload, user):
        return self._action_name

    def get_action_params(self, payload, user):
        callback_id = user.message.callback_id
        return user.behaviors.get_callback_action_params(callback_id)

    def run(self, payload, user):
        callback_id = user.message.callback_id
        action_params = self.get_action_params(payload, user)
        action_name = self.get_action_name(payload, user)
        params = {
            log_const.KEY_NAME: "handling_respond",
            "callback_id": str(callback_id),
            "process_time": self.get_processing_time(user),
            "action_name": action_name
        }

        if user.behaviors.has_callback(callback_id):
            action_params = self.get_action_params(payload, user)
            params["to_message_name"] = action_params.get(TO_MESSAGE_NAME)
            log("HandlerRespond with action %(action_name)s started respond on %(to_message_name)s", user, params)
        else:
            log("HandlerRespond with action %(action_name)s started without callback", user, params)

        text_preprocessing_result = TextPreprocessingResult(payload.get("message", {}))

        smart_kit_metrics.counter_incoming(self.app_name, user.message.message_name, self.__class__.__name__, user)

        params = {
            log_const.KEY_NAME: log_const.NORMALIZED_TEXT_VALUE,
            "normalized_text": str(text_preprocessing_result.raw),
        }
        log("text preprocessing result: '%(normalized_text)s'", user, params, level="DEBUG")

        action = user.descriptions["external_actions"][action_name]
        return action.run(user, text_preprocessing_result, action_params)

    @staticmethod
    def get_processing_time(user):
        callback_id = user.message.callback_id
        process_time = None
        callback_params = user.behaviors.get_callback_action_params(callback_id) or {}
        if SEND_TIMESTAMP in callback_params:
            process_time = time() - callback_params[SEND_TIMESTAMP]
            process_time = int(process_time * 1000)
        return process_time
