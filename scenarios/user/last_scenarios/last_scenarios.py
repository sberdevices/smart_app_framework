# coding: utf-8


class LastScenarios:
    def __init__(self, items, description, user):
        self.scenarios_names = items or []
        self.description = description
        self.user = user

    def add(self, scenario_name, text_preprocessing_result):
        if not self.scenarios_names or scenario_name != self.scenarios_names[-1]:
            self._clear(scenario_name, text_preprocessing_result)
            self.scenarios_names.append(scenario_name)

    def _clear(self, scenario_name, text_preprocessing_result):
        count = self.description.get_count(text_preprocessing_result, self.user)
        if len(self.scenarios_names) >= count:
            last_scenario = self.scenarios_names[0]
            self.delete(last_scenario)
            self.user.forms.clear_form(last_scenario)
        if scenario_name in self.scenarios_names:
            self.scenarios_names.remove(scenario_name)

    def delete(self, scenario_name):
        if scenario_name in self.scenarios_names:
            self.scenarios_names.remove(scenario_name)


    @property
    def last_scenario_name(self):
        return self.scenarios_names[-1] if self.scenarios_names else None

    def clear_all(self):
        self.scenarios_names = []

    def expire(self):
        to_remove = []
        scenario_descriptions = self.user.descriptions["scenarios"]
        forms = self.user.forms
        for scenario_id in self.scenarios_names:
            if scenario_id not in scenario_descriptions:
                to_remove.append(scenario_id)
                continue

            scenario_description = scenario_descriptions[scenario_id]

            if not hasattr(scenario_description, "form_type"):
                to_remove.append(scenario_id)
                continue

            form_key = scenario_description.form_type
            if not forms[form_key]:
                to_remove.append(scenario_id)

        for scenario_id in to_remove:
            self.delete(scenario_id)

    @property
    def raw(self):
        return self.scenarios_names
