# coding: utf-8
import sys
import traceback
from lazy import lazy

from core.descriptions.descriptions import Descriptions
from core.logging.logger_utils import log
from core.utils.exception_handlers import exc_handler

import scenarios.logging.logger_constants as log_const
from smart_kit.handlers.handle_close_app import HandlerCloseApp
from smart_kit.names.message_names import MESSAGE_TO_SKILL, LOCAL_TIMEOUT, RUN_APP, SERVER_ACTION, CLOSE_APP
from smart_kit.handlers.handle_respond import HandlerRespond
from smart_kit.handlers.handler_text import HandlerText
from smart_kit.handlers.handler_timeout import HandlerTimeout
from smart_kit.handlers.handle_server_action import HandlerServerAction
from smart_kit.resources import SmartAppResources
from smart_kit.utils import get_callback_action_params, set_debug_info
from smart_kit.utils.monitoring import smart_kit_metrics


class SmartAppModel:

    def __init__(self, resources: SmartAppResources, dialogue_manager_cls, custom_settings, **kwargs):
        log(
            f"{self.__class__.__name__}.__init__ started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE}
        )
        self.resources = resources
        self.template_settings = custom_settings["template_settings"]
        self.app_name = custom_settings.app_name
        self.dialogue_manager = dialogue_manager_cls(scenario_descriptions=self.scenario_descriptions,
                                                     app_name=self.app_name)

        handler_text = HandlerText(self.app_name, dialogue_manager=self.dialogue_manager)

        self._handlers = {
            MESSAGE_TO_SKILL: handler_text,
            RUN_APP: handler_text,
            LOCAL_TIMEOUT: HandlerTimeout(self.app_name),
            SERVER_ACTION: HandlerServerAction(self.app_name),
            CLOSE_APP: HandlerCloseApp(self.app_name)
        }
        self._handlers.update({
            message_name: HandlerRespond(self.app_name, action_name=action_name)
            for message_name, action_name in self.resources.get("responses", {}).items()
        })

        log(
            f"{self.__class__.__name__}.__init__ finished.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE}
        )

    def get_handler(self, message_type):
        return self._handlers[message_type]

    @exc_handler(on_error_obj_method_name="on_answer_error")
    def answer(self, message, user):
        user.expire()
        handler = self.get_handler(message.type)

        if not user.load_error:
            commands = handler.run(message.payload, user)
        else:
            log("Error in loading user data", user, level="ERROR", exc_info=True)
            raise Exception("Error in loading user data")

        return commands

    def on_answer_error(self, message, user):
        user.do_not_save = True
        smart_kit_metrics.counter_exception(self.app_name)
        params = {log_const.KEY_NAME: log_const.DIALOG_ERROR_VALUE,
                  "message_id": user.message.incremental_id}

        log("exc_handler: Failed to process message. Exception occurred. Fail in MESSAGE: {}".format(user.message.masked_value),
            user, params, level="ERROR", exc_info=True)

        callback_action_params = get_callback_action_params(user)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        error = '\n'.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        if user.settings["template_settings"].get("debug_info"):
            set_debug_info(self.app_name, callback_action_params, error)
        exception_action = user.descriptions["external_actions"]["exception_action"]
        commands = exception_action.run(user=user, text_preprocessing_result=None,
                                        params=callback_action_params)
        return commands


    @lazy
    def scenario_descriptions(self):
        return Descriptions(self.resources.registered_repositories)
