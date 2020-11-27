# coding: utf-8
from core.descriptions.smart_updatable_lazy_descriptions import SmartUpdatableLazyDescriptions
from scenarios.scenario_models.forms.form_description import form_description_factory


class FormsDescription(SmartUpdatableLazyDescriptions):
    def __init__(self, items):
        super(FormsDescription, self).__init__(form_description_factory, items)
