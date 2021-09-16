# coding: utf-8
from core.logging.logger_utils import log
from core.names import field

import scenarios.logging.logger_constants as log_const
from lazy import lazy

from scenarios.scenario_descriptions.form_filling_scenario import FormFillingScenario
from smart_kit.system_answers.nothing_found_action import NothingFoundAction
from smart_kit.utils.monitoring import smart_kit_metrics
from scenarios.scenario_models.history import Event, HistoryConstants


class DialogueManager:
    NOTHING_FOUND_ACTION = "nothing_found_action"

    def __init__(self, scenario_descriptions, app_name, **kwargs):
        log(f"{self.__class__.__name__}.__init__ started.",
                      params={log_const.KEY_NAME: log_const.STARTUP_VALUE})
        self.scenario_descriptions = scenario_descriptions
        self.scenarios = scenario_descriptions["scenarios"]
        self.scenario_keys = set(self.scenarios.get_keys())
        self.actions = scenario_descriptions["external_actions"]
        self.app_name = app_name
        log(f"{self.__class__.__name__}.__init__ finished.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE})

    @lazy
    def _nothing_found_action(self):
        return self.actions.get(self.NOTHING_FOUND_ACTION) or NothingFoundAction()

    def run(self, text_preprocessing_result, user):
        last_scenarios = user.last_scenarios
        scenarios_names = last_scenarios.scenarios_names
        scenario_key = user.message.payload[field.INTENT]

        if scenario_key in scenarios_names:
            scenario = self.scenarios[scenario_key]

            is_form_filling = isinstance(scenario, FormFillingScenario)
            field_ = None
            form = None
            if is_form_filling:
                form = scenario._get_form(user)
                field_ = scenario._field(form, text_preprocessing_result, user, None)

            if not scenario.text_fits(text_preprocessing_result, user):
                is_form_filling = isinstance(scenario, FormFillingScenario)
                if is_form_filling and field_:
                    has_ask_again = field_.description.has_requests
                    if has_ask_again and field_.description.ask_again_times_left > 0:
                        field_.description.ask_again_times_left -= 1
                        user.history.add_event(
                            Event(type=HistoryConstants.types.FIELD_EVENT,
                                  scenario=scenario.root_id,
                                  content={HistoryConstants.content_fields.FIELD: field_.description.id},
                                  results=HistoryConstants.event_results.ASK_QUESTION))
                        reply = scenario.get_reply(
                            user, text_preprocessing_result, scenario.actions, field_, form)
                        return reply, True

                smart_kit_metrics.counter_nothing_found(self.app_name, scenario_key, user)

                return self._nothing_found_action.run(user, text_preprocessing_result), False

            if is_form_filling and field_:
                field_.description.ask_again_times_left = field_.description.ask_again_times

        return self.run_scenario(scenario_key, text_preprocessing_result, user), True

    def run_scenario(self, scen_id, text_preprocessing_result, user):
        initial_last_scenario = user.last_scenarios.last_scenario_name
        scenario = self.scenarios[scen_id]
        params = {log_const.KEY_NAME: log_const.CHOSEN_SCENARIO_VALUE,
                  log_const.CHOSEN_SCENARIO_VALUE: scen_id,
                  log_const.SCENARIO_DESCRIPTION_VALUE: scenario.scenario_description
                  }
        log(log_const.LAST_SCENARIO_MESSAGE, user, params)
        run_scenario_result = scenario.run(text_preprocessing_result, user)

        actual_last_scenario = user.last_scenarios.last_scenario_name
        if actual_last_scenario and actual_last_scenario != initial_last_scenario:
            smart_kit_metrics.counter_scenario_change(self.app_name, actual_last_scenario, user)

        return run_scenario_result
