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
            "message": self._user.message,
            "payload": self._user.message.payload,
            "uuid": self._user.message.uuid,
            "forms": forms,
            "main_form": main_form,
            "text_preprocessing_result": tpr_data,
            "variables": self._user.variables.values,
            "counters": self._user.counters.raw,
            "scenario_id": self._user.last_scenarios.last_scenario_name,
            "gender_sensitive_text": self._user.gender_selector.get_text_by_key
        }
        return data
