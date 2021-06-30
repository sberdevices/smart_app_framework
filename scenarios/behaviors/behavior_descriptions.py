# coding: utf-8
from core.descriptions.smart_updatable_descriptions_items import SmartUpdatableDescriptionsItems
from scenarios.behaviors.behavior_description import BehaviorDescription


class BehaviorDescriptions(SmartUpdatableDescriptionsItems):
    def __init__(self, items):
        super(BehaviorDescriptions, self).__init__(BehaviorDescription, items)
