# coding: utf-8

from scenarios.scenario_models.forms.form import form_model_factory
from core.model.lazy_items import LazyItems


class Forms(LazyItems):
    def __init__(self, items, descriptions, user):
        super(Forms, self).__init__(items, descriptions, user, form_model_factory)

    def __getitem__(self, description):
        if hasattr(description, "id"):
            id = description.id
        else:
            id = description
            description = self._descriptions.get(id)
        form = self._items.get(description)
        raw_data = self._raw_items.get(id)
        if form is None and raw_data is not None:
            form = self._build_factory(description, raw_data)
            self._items[description] = form
        return form

    def get_or_create(self, key):
        form = self[key]
        return form or self.new(key)

    def remove_item(self, descr_id):
        if descr_id in self._raw_items:
            self._raw_items.pop(descr_id)
            description = self._descriptions.get(descr_id)
            if description and description in self._items:
                self._items.pop(description)

    def new(self, descr_id):
        self.remove_item(descr_id)
        description = self._descriptions[descr_id]
        form = self._build_factory(description, {})
        self._items[description] = form
        form.touch()
        return form

    def collect_form_fields(self):
        fields = {}
        for form in self.raw:
            if form in self.descriptions:
                inner_form = self[form]
                data = inner_form.get_fields_values()
                fields.update(data)
        return fields

    def expire(self):
        to_remove = []
        descr_keys = self.descriptions.keys()
        for description_id in self.raw:
            if description_id in descr_keys:
                
                item = self[description_id]
                if item and item.check_expired():
                    to_remove.append(description_id)
            else:
                to_remove.append(description_id)
        for descr_id in to_remove:
            self.remove_item(descr_id)

    def clear_all(self):
        self._raw_items.clear()
        self._items.clear()

    def clear_form(self, scenario_name):
        scenario_descriptions = self._user.descriptions["scenarios"]
        if scenario_name in scenario_descriptions:
            scenario = scenario_descriptions[scenario_name]
            if not scenario.keep_forms_alive:
                self._user.forms.remove_item(scenario.form_type)
