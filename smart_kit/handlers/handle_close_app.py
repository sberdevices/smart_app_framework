from core.logging.logger_utils import log
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
import scenarios.logging.logger_constants as log_const
from scenarios.actions.action import ClearCurrentScenarioAction

from smart_kit.handlers.handler_base import HandlerBase


class HandlerCloseApp(HandlerBase):
    def __init__(self, app_name):
        super(HandlerCloseApp, self).__init__(app_name)
        self._clear_current_scenario = ClearCurrentScenarioAction(None)

    def run(self, payload, user):
        super().run(payload, user)
        text_preprocessing_result = TextPreprocessingResult(payload.get("message", {}))
        params = {
            log_const.KEY_NAME: "HandlerCloseApp",
            "tpr_str": str(text_preprocessing_result.raw)
        }
        self._clear_current_scenario.run(user, text_preprocessing_result)
        log("HandlerCloseApp with text preprocessing result", user, params)
