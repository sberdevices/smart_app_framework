from core.basic_models.parametrizers.parametrizer import BasicParametrizer


class Parametrizer(BasicParametrizer):

    def __init__(self, user, items):
        super(Parametrizer, self).__init__(user, items)

    def _get_scenario(self):
        scenario_id = self._user.last_scenarios.last_scenario_name
        return self._user.descriptions["scenarios"].get(scenario_id) if scenario_id else None

    def _get_main_form(self, forms):
        scenario = self._get_scenario()
        if scenario:
            return forms[scenario.form_type]
        return None

    def _get_user_data(self, text_preprocessing_result=None):
        tpr_data = text_preprocessing_result.raw if text_preprocessing_result else {}
        forms = self._user.forms.collect_form_fields()
        main_form = self._get_main_form(forms)
        data = {
            "counters": self._user.counters.raw,
            "forms": forms,
            "gender_sensitive_text": self._user.gender_selector.get_text_by_key,
            "local_vars": self._user.local_vars.values,
            "main_form": main_form,
            "message": self._user.message,
            "payload": self._user.message.payload,
            "scenario_id": self._user.last_scenarios.last_scenario_name,
            "text_preprocessing_result": tpr_data,
            "uuid": self._user.message.uuid,
            "variables": self._user.variables.values,
        }
        return data
