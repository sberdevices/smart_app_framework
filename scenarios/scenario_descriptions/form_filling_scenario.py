# coding: utf-8
from typing import Dict, Any
from core.basic_models.scenarios.base_scenario import BaseScenario
from core.monitoring.monitoring import monitoring
from core.logging.logger_utils import log
import scenarios.logging.logger_constants as log_const
from scenarios.scenario_models.history import Event, HistoryConstants

FORM_FIELD_DELIMETER = "__"


class FormFillingScenario(BaseScenario):
    def __init__(self, items, id):
        super(FormFillingScenario, self).__init__(items, id)
        self.form_type = items["form"]
        self.keep_forms_alive = items.get("keep_form_alive", False)
        self.tag = items.get("tag")

    def text_fits(self, text_preprocessing_result, user):
        return self._check_question_field(text_preprocessing_result, user, None)


    def get_ask_again_question_result(self, text_preprocessing_result, user, params):
        form = user.forms[self.form_type]
        question_field = self._question_field(form, text_preprocessing_result, user, params)
        question = question_field.description.ask_again_question
        return question.run(user, text_preprocessing_result, params)

    def check_ask_again_question(self, text_preprocessing_result, user, params):
        form = user.forms[self.form_type]
        question_field = self._question_field(form, text_preprocessing_result, user, params)
        return question_field.description.has_again_question

    def _check_question_field(self, text_preprocessing_result, user, params):
        form = user.forms[self.form_type]
        question_field = self._question_field(form, text_preprocessing_result, user, params)
        return question_field.check_can_be_filled(text_preprocessing_result, user) if question_field else False

    def _question_field(self, form, text_preprocessing_result, user, params):
        return self._find_question_field(form, text_preprocessing_result, user, params)

    def _find_question_field(self, form, text_preprocessing_result, user, params):
        question_field = None
        for field_name in form.fields.descriptions:
            field = form.fields[field_name]
            if not field.valid and field.description.has_questions and field.description.requirement.check(
                    text_preprocessing_result, user, params
            ):
                question_field = field
                break
        return question_field

    def check_comment_field(self, text_preprocessing_result, user, params=None):
        form = self._get_form(user)
        question_field = self._question_field(form, text_preprocessing_result, user, params)
        return question_field.description.is_comment if question_field else False

    def _extract(self, form, text_normalization_result, user, params):
        result = {}
        for field_key, field_descr in form.description.fields.items():
            field = form.fields[field_key]
            if field.available:
                check = field_descr.requirement.check(text_normalization_result, user, params)
                log_params = self._log_params()
                log_params["requirement"] = field_descr.requirement.__class__.__name__,
                log_params["requirement_check_result"] = check
                log_params["field_key"] = str(field_key)
                message = "FormFillingScenario.extract: field %(field_key)s requirement %(requirement)s return value: %(requirement_check_result)s"
                log(message, user, log_params)
                if check:
                    result[field_key] = field_descr.filler.run(user, text_normalization_result, params)
                    event = Event(type=HistoryConstants.types.FIELD_EVENT,
                                  scenario=self.root_id,
                                  content={HistoryConstants.content_fields.FIELD: field_key},
                                  results=HistoryConstants.event_results.FILLED)
                    user.history.add_event(event)
        return result

    def _get_validation_error_msg(self, user, text_preprocessing_result, form, data_extracted, params):
        error_msgs = []
        for field_key, field in form.description.fields.items():
            value = data_extracted.get(field_key)
            # is not None is necessary, because 0 and False should be checked, None - shouldn't fill
            if value is not None and not field.field_validator.requirement.check(value, params):
                params = {
                    log_const.KEY_NAME: log_const.SCENARIO_RESULT_VALUE,
                    "field_key": field_key
                }
                message = "Field is not valid: %(field_key)s"
                log(message, user, params)
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

    def _get_form(self, user):
        form = user.forms.get_or_create(self.form_type)
        form = user.forms.new(self.form_type) if form.is_valid()  else form
        form.refresh()
        return form

    def get_reply(self, user, text_preprocessing_result, reply_actions, question_field, form):
        if question_field:
            question_field.set_available()
            actions = question_field.description.questions
            params = {
                log_const.KEY_NAME: log_const.SCENARIO_RESULT_VALUE,
                "field": question_field.description.id
            }
            message = "Ask question on field: %(field)s"
            log(message, user, params)
            action_messages = self.get_action_results(user, text_preprocessing_result, actions)
        else:
            actions = reply_actions
            params = {
                log_const.KEY_NAME: log_const.SCENARIO_RESULT_VALUE,
                "id": self.id
            }
            message = "Finished scenario: %(id)s"
            log(message, user, params)
            user.preprocessing_messages_for_scenarios.clear()
            action_messages = self.get_action_results(user, text_preprocessing_result, actions)
            user.last_scenarios.delete(self.id)
        return action_messages

    def get_fields_data(self, form, form_key):
        form_fields_data = {}
        for field_key, field_value in form.fields.values.items():
            key = "".join((self._clean_key(form_key), FORM_FIELD_DELIMETER, self._clean_key(field_key)))
            form_fields_data[key] = field_value
        return form_fields_data

    def _clean_key(self, key: str):
        return key.replace(" ", "")

    @monitoring.got_histogram("scenario_time")
    def run(self, text_preprocessing_result, user, params: Dict[str, Any] = None):
        form = self._get_form(user)
        user.last_scenarios.add(self.id, text_preprocessing_result)
        user.preprocessing_messages_for_scenarios.add(text_preprocessing_result)
        data_extracted = self._extract(form, text_preprocessing_result, user, params)
        log("Extracted data={}".format(data_extracted), user, self._log_params())
        validation_error_msg = self._get_validation_error_msg(user, text_preprocessing_result, form, data_extracted,
                                                              params)
        if validation_error_msg:
            # got validation msg, ask question
            reply_messages = validation_error_msg
        else:
            reply_messages, is_break = self._fill_form(user, text_preprocessing_result, form, data_extracted)
            if not is_break:
                question_field = self._question_field(form, text_preprocessing_result, user, params)
                if question_field:
                    user.history.add_event(
                        Event(type=HistoryConstants.types.FIELD_EVENT,
                              scenario=self.root_id,
                              content={HistoryConstants.content_fields.FIELD: question_field.description.id},
                              results=HistoryConstants.event_results.ASK_QUESTION))
                reply = self.get_reply(user, text_preprocessing_result, self.actions, question_field, form)
                reply_messages.extend(reply)

        if not reply_messages:
            reply_messages = self.get_no_commands_action(user, text_preprocessing_result)

        return reply_messages
