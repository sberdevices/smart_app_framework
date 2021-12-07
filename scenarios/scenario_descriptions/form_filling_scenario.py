# coding: utf-8
from typing import Dict, Any

from core.basic_models.scenarios.base_scenario import BaseScenario
from core.monitoring.monitoring import monitoring
from core.logging.logger_utils import log

import scenarios.logging.logger_constants as log_const
from scenarios.scenario_models.field.field import QuestionField
from scenarios.scenario_models.history import Event, HistoryConstants
from scenarios.actions.action_params_names import REQUEST_FIELD

FORM_FIELD_DELIMETER = "__"


class FormFillingScenario(BaseScenario):
    def __init__(self, items, id):
        super(FormFillingScenario, self).__init__(items, id)
        self.form_type = items["form"]
        self.keep_forms_alive = items.get("keep_form_alive", False)
        self.tag = items.get("tag")

    def _get_form(self, user):
        form = user.forms.get_or_create(self.form_type)
        form = user.forms.new(self.form_type) if form.is_valid() else form
        form.refresh()
        return form

    def text_fits(self, text_preprocessing_result, user):
        return self._check_field(text_preprocessing_result, user, None)

    def check_ask_again_requests(self, text_preprocessing_result, user, params):
        form = user.forms[self.form_type]
        question_field = self._field(form, text_preprocessing_result, user, params)
        return question_field.ask_again_counter < len(question_field.description.ask_again_requests)

    def ask_again(self, text_preprocessing_result, user, params):
        form = user.forms[self.form_type]
        question_field = self._field(form, text_preprocessing_result, user, params)
        question = question_field.description.ask_again_requests[question_field.ask_again_counter]
        question_field.ask_again_counter += 1

        user.history.add_event(
            Event(type=HistoryConstants.types.FIELD_EVENT,
                  scenario=self.root_id,
                  content={HistoryConstants.content_fields.FIELD: question_field.description.id},
                  results=HistoryConstants.event_results.ASK_QUESTION))

        return question.run(user, text_preprocessing_result, params)

    def _check_field(self, text_preprocessing_result, user, params):
        form = user.forms[self.form_type]
        field = self._field(form, text_preprocessing_result, user, params)
        return field.check_can_be_filled(text_preprocessing_result, user) if field else False

    def _field(self, form, text_preprocessing_result, user, params):
        return self._find_field(form, text_preprocessing_result, user, params)

    def _find_field(self, form, text_preprocessing_result, user, params):
        for field_name in form.fields.descriptions:
            field = form.fields[field_name]
            if not field.valid and field.description.has_requests and \
                    field.description.requirement.check(
                    text_preprocessing_result, user, params
                    ):
                return field

    def get_fields_data(self, form, form_key):
        form_fields_data = {}
        for field_key, field_value in form.fields.values.items():
            key = "".join((self._clean_key(form_key), FORM_FIELD_DELIMETER, self._clean_key(field_key)))
            form_fields_data[key] = field_value
        return form_fields_data

    def _clean_key(self, key: str):
        return key.replace(" ", "")

    def _extract_by_field_filler(self, field_key, field_descr, text_normalization_result, user, params):
        result = {}
        check = field_descr.requirement.check(text_normalization_result, user, params)
        log_params = self._log_params()
        log_params["requirement"] = field_descr.requirement.__class__.__name__,
        log_params["check"] = check
        log_params["field_key"] = field_key
        message = "FormFillingScenario.extract: field %(field_key)s requirement %(requirement)s return value: %(check)s"
        log(message, user, log_params)
        if check:
            result[field_key] = field_descr.filler.run(user, text_normalization_result, params)
            event = Event(type=HistoryConstants.types.FIELD_EVENT,
                          scenario=self.root_id,
                          content={HistoryConstants.content_fields.FIELD: field_key},
                          results=HistoryConstants.event_results.FILLED)
            user.history.add_event(event)
        return result

    def _extract_data(self, form, text_normalization_result, user, params):
        result = {}

        callback_id = user.message.callback_id
        action_params = user.behaviors.get_callback_action_params(callback_id) or {}
        request_field = action_params.get(REQUEST_FIELD)
        if request_field and request_field["type"] == "integration":
            field = form.fields[request_field["id"]]
            field_descr = form.description.fields[request_field["id"]]
            if field.available:
                result.update(self._extract_by_field_filler(request_field["id"], field_descr, text_normalization_result,
                                                            user, params))
        else:
            for field_key, field_descr in form.description.fields.items():
                field = form.fields[field_key]
                if field.available and isinstance(field, QuestionField):
                    result.update(self._extract_by_field_filler(field_key, field_descr,
                                                                text_normalization_result, user, params))
        return result

    def _validate_extracted_data(self, user, text_preprocessing_result, form, data_extracted, params):
        error_msgs = []
        for field_key, field in form.description.fields.items():
            value = data_extracted.get(field_key)
            # is not None is necessary, because 0 and False should be checked, None - shouldn't fill
            if value is not None and not field.field_validator.requirement.check(value, params):
                log_params = {
                    log_const.KEY_NAME: log_const.SCENARIO_RESULT_VALUE,
                    "field_key": field_key
                }
                message = "Field is not valid: %(field_key)s"
                log(message, user, log_params)
                actions = field.field_validator.actions
                error_msgs = self.get_action_results(user, text_preprocessing_result, actions)
                break
        return error_msgs

    def _fill_form(self, user, text_preprocessing_result, form, data_extracted):
        on_filled_actions = []
        fields = form.fields
        scenario_model = user.scenario_models[self.id]
        is_break = False
        for description in fields:
            key = description.id
            value = data_extracted.get(key)
            field = fields[key]
            if field.fill(value):
                _action = self.get_action_results(user=user, text_preprocessing_result=text_preprocessing_result,
                                                  actions=field.description.on_filled_actions)
                on_filled_actions.extend(_action)
                if scenario_model.break_scenario:
                    is_break = True
                    return _action, is_break
        return on_filled_actions, is_break

    def get_reply(self, user, text_preprocessing_result, reply_actions, field, form):
        action_params = {}
        if field:
            field.set_available()
            actions = field.description.requests
            params = {
                log_const.KEY_NAME: log_const.SCENARIO_RESULT_VALUE,
                "field": field.description.id
            }
            message = "Ask question on field: %(field)s"
            log(message, user, params)
            action_params[REQUEST_FIELD] = {"type": field.description.type, "id": field.description.id}
            action_messages = self.get_action_results(user, text_preprocessing_result, actions, action_params)
        else:
            actions = reply_actions
            params = {
                log_const.KEY_NAME: log_const.SCENARIO_RESULT_VALUE,
                "id": self.id
            }
            message = "Finished scenario: %(id)s"
            log(message, user, params)
            user.preprocessing_messages_for_scenarios.clear()
            action_messages = self.get_action_results(user, text_preprocessing_result, actions, action_params)
            user.last_scenarios.delete(self.id)
        return action_messages

    @monitoring.got_histogram("scenario_time")
    def run(self, text_preprocessing_result, user, params: Dict[str, Any] = None):
        form = self._get_form(user)
        user.last_scenarios.add(self.id, text_preprocessing_result)
        user.preprocessing_messages_for_scenarios.add(text_preprocessing_result)

        data_extracted = self._extract_data(form, text_preprocessing_result, user, params)
        logging_params = {"data_extracted_str": str(data_extracted)}
        logging_params.update(self._log_params())
        log("Extracted data=%(data_extracted_str)s", user, logging_params)

        validation_error_msg = self._validate_extracted_data(user, text_preprocessing_result, form, data_extracted, params)
        if validation_error_msg:
            reply_messages = validation_error_msg
        else:
            reply_messages, is_break = self._fill_form(user, text_preprocessing_result, form, data_extracted)
            if not is_break:
                field = self._field(form, text_preprocessing_result, user, params)
                if field:
                    user.history.add_event(
                        Event(type=HistoryConstants.types.FIELD_EVENT,
                              scenario=self.root_id,
                              content={HistoryConstants.content_fields.FIELD: field.description.id},
                              results=HistoryConstants.event_results.ASK_QUESTION))
                reply = self.get_reply(user, text_preprocessing_result, self.actions, field, form)
                reply_messages.extend(reply)

        if not reply_messages:
            reply_messages = self.get_no_commands_action(user, text_preprocessing_result)

        return reply_messages
