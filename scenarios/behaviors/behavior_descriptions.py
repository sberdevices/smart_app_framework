# coding: utf-8
from core.descriptions.smart_updatable_lazy_descriptions import SmartUpdatableLazyDescriptions
from scenarios.behaviors.behavior_description import BehaviorDescription


class BehaviorDescriptions(SmartUpdatableLazyDescriptions):
    def __init__(self, items):
        super(BehaviorDescriptions, self).__init__(BehaviorDescription, items)
