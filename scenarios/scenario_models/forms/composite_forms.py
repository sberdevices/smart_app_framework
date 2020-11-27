from scenarios.scenario_models.forms.form import BaseForm
from scenarios.scenario_models.forms.forms import Forms


class CompositeForm(BaseForm):
    def __init__(self, items, description, user):
        super(CompositeForm, self).__init__(items, description, user)
        items = items or {}
        self.forms = Forms(items.get("forms"), description.forms, user)
        self._valid = items.get("valid") or self.description.valid

    def is_valid(self):
        return self._valid

    def set_valid(self):
        self._valid = True

    def get_fields_values(self):
        data = {}
        for form in self.description.forms.keys():
            inner_form = self.forms[form]
            fields = inner_form.get_fields_values() if inner_form else {form: {}}
            data.update(fields)
        return {self.description.id: data}

    @property
    def raw(self):
        raw = {"valid": self._valid}
        if self.forms.raw:
            raw["forms"] = self.forms.raw
        if self.remove_time:
            raw["remove_time"] = self.remove_time
        return raw
