from core.descriptions.smart_updatable_descriptions_items import SmartUpdatableDescriptionsItems
from scenarios.scenario_models.field.field_filler_description import field_filler_factory


class ExternalFieldFillerDescriptions(SmartUpdatableDescriptionsItems):
    def __init__(self, items):
        super(ExternalFieldFillerDescriptions, self).__init__(field_filler_factory, items, ordered=True)
