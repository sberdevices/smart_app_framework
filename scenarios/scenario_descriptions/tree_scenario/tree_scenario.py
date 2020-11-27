# coding: utf-8
from lazy import lazy
from typing import Dict, Any
from scenarios.scenario_descriptions.form_filling_scenario import FormFillingScenario
from scenarios.scenario_descriptions.tree_scenario.tree_scenario_node import TreeScenarioNode
from core.model.factory import dict_factory
from core.monitoring.monitoring import monitoring
from core.logging.logger_utils import log
import scenarios.logging.logger_constants as log_const
from scenarios.scenario_models.history import Event, HistoryConstants

MAIN_INNER_FORM_DELIMETER = "__"


class TreeScenario(FormFillingScenario):
    def __init__(self, items, id):
        super(TreeScenario, self).__init__(items, id)
        self._start_node_key = items["start_node_key"]
        self._scenario_nodes = items["scenario_nodes"]

    @lazy
    @dict_factory(TreeScenarioNode)
    def scenario_nodes(self):
        return self._scenario_nodes

    def _question_field(self, form, text_preprocessing_result, user, params):
        current_node = self.get_current_node(user)
        internal_form = self._get_internal_form(form.forms, current_node.form_key)
        return self._find_question_field(internal_form, text_preprocessing_result, user, params)

    def _set_current_node_id(self, user, node_id):
        user.scenario_models[self.id].current_node = node_id

    def _add_loop_count(self, user, node_id):
        user.scenario_models[self.id].add_count(node_id)

    def _remove_current_node_id(self, user):
        user.scenario_models[self.id].current_node = None

    def get_current_node(self, user):
        current_node_id = user.scenario_models[self.id].current_node
        current_node = self.scenario_nodes[current_node_id]
        return current_node

    def get_next_node(self, user, node, text_preprocessing_result, params):
        available_node_keys = node.available_nodes
        for key in available_node_keys:
            node = self.scenario_nodes[key]
            log_params = {log_const.KEY_NAME: log_const.CHECKING_NODE_ID_VALUE,
                          log_const.CHECKING_NODE_ID_VALUE: node.id}
            log(log_const.CHECKING_NODE_ID_MESSAGE, user, log_params)
            requirement_result = node.requirement.check(text_preprocessing_result, user, params)
            if requirement_result:
                log_params = {log_const.KEY_NAME: log_const.CHOSEN_NODE_ID_VALUE,
                              log_const.CHOSEN_NODE_ID_VALUE: node.id}
                log(log_const.CHOSEN_NODE_ID_MESSAGE, user, log_params)
                self._add_loop_count(user, node.id)
                return node

    def _get_form(self, user):
        forms = user.forms
        form = forms[self.form_type]
        if not form or form.is_valid():
            form = forms.new(self.form_type)
            user.scenario_models[self.id].current_node = self._start_node_key
        else:
            form.touch()
        return form

    def _get_internal_form(self, forms, form_key):
        if form_key is not None:
            return forms[form_key] or forms.new(form_key)

    def get_fields_data(self, main_form, form_type):
        all_forms_fields = {}
        for node_id in self.scenario_nodes:
            inner_form_key = self.scenario_nodes[node_id].form_key
            form = self._get_internal_form(main_form.forms, inner_form_key)
            if form:
                main_inner_forms_key = "".join(
                    (self._clean_key(form_type), MAIN_INNER_FORM_DELIMETER, self._clean_key(inner_form_key)))
                form_field_data = super(TreeScenario, self).get_fields_data(form, main_inner_forms_key)
                all_forms_fields.update(form_field_data)
        return all_forms_fields

    @monitoring.got_histogram("scenario_time")
    def run(self, text_preprocessing_result, user, params: Dict[str, Any] = None):
        main_form = self._get_form(user)
        user.last_scenarios.add(self.id, text_preprocessing_result)
        user.preprocessing_messages_for_scenarios.add(text_preprocessing_result)
        current_node = self.get_current_node(user)
        new_node = current_node
        self._add_loop_count(user, new_node.id)
        internal_form, question_form = None, None
        fill_other = True
        on_filled_actions = []

        while new_node:
            current_node = new_node
            log("message id: {}, current scenario: {}, current node: {}".format(
                user.message.incremental_id, self.id, current_node.id), user, self._log_params())
            internal_form = self._get_internal_form(main_form.forms, current_node.form_key)
            data_extracted = {}

            validation_error_msg = None
            for field_key, field_descr in internal_form.description.fields.items():
                field = internal_form.fields[field_key]
                if field.available:
                    extracted = field_descr.filler.run(user, text_preprocessing_result, params)
                    if extracted is not None:
                        event = Event(type=HistoryConstants.types.FIELD_EVENT,
                                      scenario=self.root_id,
                                      node=current_node.id,
                                      content={HistoryConstants.content_fields.FIELD: field_key},
                                      results=HistoryConstants.event_results.FILLED)
                        user.history.add_event(event)
                        log_params = self._log_params()
                        log_params["message_id"] = user.message.incremental_id
                        log_params["field_key"] = field_key
                        log_params["extracted"] = extracted
                        log("message id: %(message_id)s, extracted data for field %(field_key)s: "
                            "%(extracted)s", user, log_params)
                    if extracted is not None and fill_other:
                        fill_other = fill_other and field_descr.fill_other
                        field_data = {field_key: extracted}
                        _validation_error_msg = self._get_validation_error_msg(user, text_preprocessing_result,
                                                                               internal_form, field_data, params)
                        if _validation_error_msg:
                            # return only first validation message in form
                            validation_error_msg = validation_error_msg or _validation_error_msg
                        else:
                            data_extracted.update(field_data)
            on_filled_node_actions, is_break = self._fill_form(user, text_preprocessing_result,
                                                               internal_form, data_extracted)
            if is_break:
                return on_filled_node_actions
            on_filled_actions.extend(on_filled_node_actions)

            if validation_error_msg is not None:
                return validation_error_msg

            if internal_form.is_valid():
                if not current_node.available_nodes and not question_form:
                    # end node found
                    main_form.set_valid()
                    self._remove_current_node_id(user)
                    event = Event(
                        type=HistoryConstants.types.END_SCENARIO,
                        scenario=self.root_id,
                        node=current_node.id,
                        results=HistoryConstants.event_results.SUCCESS
                    )
                    user.history.add_event(event)
                    break

            elif not question_form:
                question_form = internal_form
                self._set_current_node_id(user, current_node.id)
            new_node = self.get_next_node(user, current_node, text_preprocessing_result, params)

        question_field = self._find_question_field(question_form, text_preprocessing_result,
                                                   user, params) if question_form else None
        reply_commands = on_filled_actions
        if question_field:
            event = Event(type=HistoryConstants.types.FIELD_EVENT,
                          scenario=self.root_id,
                          node=current_node.id,
                          content={HistoryConstants.content_fields.FIELD: question_field.description.id},
                          results=HistoryConstants.event_results.ASK_QUESTION)
            user.history.add_event(event)
        _command = self.get_reply(user, text_preprocessing_result, current_node.actions, question_field, main_form)
        reply_commands.extend(_command)

        if not reply_commands:
            reply_commands = self.get_no_commands_action(user, text_preprocessing_result)

        return reply_commands
