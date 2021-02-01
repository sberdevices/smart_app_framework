from core.logging.logger_utils import log

from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
import scenarios.logging.logger_constants as log_const

from smart_kit.handlers.handler_base import HandlerBase
from smart_kit.message.app_info import AppInfo
from core.names.field import APP_INFO
from smart_kit.names.message_names import MESSAGE_TO_SKILL, RUN_APP, SERVER_ACTION
from smart_kit.utils.monitoring import smart_kit_metrics


class HandlerRespond(HandlerBase):
    handler_name = "HandlerRespond"

    def __init__(self, app_name, action_name=None, ):
        super(HandlerRespond, self).__init__(app_name)
        self._action_name = action_name

    def get_action_name(self, payload, user):
        return self._action_name

    def get_action_params(self, payload):
        return {}

    def run(self, payload, user):
        callback_id = user.message.callback_id
        if user.behaviors.has_callback(callback_id):
            params = {log_const.KEY_NAME: "handling_respond"}
            log("HandlerRespond started", user, params)
            action_params = user.behaviors.get_callback_action_params(callback_id)
            if action_params:
                app_info = None
                for original_message_name in [MESSAGE_TO_SKILL, SERVER_ACTION, RUN_APP]:
                    if original_message_name in action_params:
                        app_info = AppInfo(action_params[original_message_name].get(APP_INFO, {}))
                        break

                smart_kit_metrics.counter_incoming(self.app_name, user.message.message_name, self.__class__.__name__,
                                                   user, app_info=app_info)

        text_preprocessing_result = TextPreprocessingResult(payload.get("message", {}))
        params = {
            log_const.KEY_NAME: log_const.NORMALIZED_TEXT_VALUE,
            "normalized_text": str(text_preprocessing_result.raw),
        }
        log("text preprocessing result: '%(normalized_text)s'", user, params)
        action_name = self.get_action_name(payload, user)
        action = user.descriptions["external_actions"][action_name]
        action_params = self.get_action_params(payload)
        return action.run(user, text_preprocessing_result, action_params)
