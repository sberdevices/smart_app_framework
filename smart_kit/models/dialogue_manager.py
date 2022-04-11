# coding: utf-8
from core.logging.logger_utils import log
from core.names import field

import scenarios.logging.logger_constants as log_const
from lazy import lazy

from scenarios.scenario_descriptions.form_filling_scenario import FormFillingScenario
from smart_kit.system_answers.nothing_found_action import NothingFoundAction
from core.monitoring.monitoring import monitoring

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
        before_action = user.descriptions["external_actions"].get("before_action")
        if before_action:
            params = user.parametrizer.collect(text_preprocessing_result)
            before_action.run(user, text_preprocessing_result, params)
        scenarios_names = user.last_scenarios.scenarios_names
        scenario_key = user.message.payload[field.INTENT]
        if scenario_key in scenarios_names:
            scenario = self.scenarios[scenario_key]
            is_form_filling = isinstance(scenario, FormFillingScenario)
            if is_form_filling:
                if not scenario.text_fits(text_preprocessing_result, user):
                    params = user.parametrizer.collect(text_preprocessing_result)
                    if scenario.check_ask_again_requests(text_preprocessing_result, user, params):
                        reply = scenario.ask_again(text_preprocessing_result, user, params)
                        return reply, True
                    monitoring.counter_nothing_found(self.app_name, scenario_key, user)
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
            monitoring.counter_scenario_change(self.app_name, actual_last_scenario, user)

        return run_scenario_result
