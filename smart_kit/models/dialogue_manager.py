# coding: utf-8
from core.logging.logger_utils import log
from core.names import field

import scenarios.logging.logger_constants as log_const
from lazy import lazy

from smart_kit.system_answers.nothing_found_action import NothingFoundAction
from smart_kit.utils.monitoring import smart_kit_metrics


class DialogueManager:
    NOTHING_FOUND_ACTION = "nothing_found_action"

    def __init__(self, scenario_descriptions, app_name, **kwargs):
        log(f"{self.__class__.__name__}.__init__ started.",
                      params={log_const.KEY_NAME: log_const.STARTUP_VALUE})
        self.scenario_descriptions = scenario_descriptions
        self.scenarios = scenario_descriptions['scenarios']
        self.scenario_keys = set(self.scenarios.get_keys())
        self.actions = scenario_descriptions["external_actions"]
        self.app_name = app_name
        log("DialogueManager.__init__ finished.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE})

    @lazy
    def _nothing_found_action(self):
        return self.actions.get(self.NOTHING_FOUND_ACTION) or NothingFoundAction()

    def run(self, text_preprocessing_result, user):
        last_scenarios = user.last_scenarios
        scenarios_names = last_scenarios.scenarios_names
        scenario_key = user.message.payload[field.INTENT]

        if scenario_key in scenarios_names:
            scenario = self.scenarios[scenario_key]
            if not scenario.text_fits(text_preprocessing_result, user):
                smart_kit_metrics.counter_nothing_found(self.app_name, scenario_key, user)

                return self._nothing_found_action.run(user, text_preprocessing_result), False

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
