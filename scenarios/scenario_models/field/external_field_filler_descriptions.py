from core.descriptions.smart_updatable_lazy_descriptions import SmartUpdatableLazyDescriptions
from scenarios.scenario_models.field.field_filler_description import field_filler_factory


class ExternalFieldFillerDescriptions(SmartUpdatableLazyDescriptions):
    def __init__(self, items):
        super(ExternalFieldFillerDescriptions, self).__init__(field_filler_factory, items, ordered=True)
