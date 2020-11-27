# coding: utf-8
from core.descriptions.lazy_descriptions import LazyDescriptions
from scenarios.user.last_scenarios.last_scenarios_description import LastScenariosDescription


class LastScenariosDescriptions(LazyDescriptions):
    DEFAULT_COUNT = 1

    def __init__(self, items):
        super(LastScenariosDescriptions, self).__init__(LastScenariosDescription, items)

    def get_count(self, text_preprocessing_result, user):
        count = self.DEFAULT_COUNT
        for key in self:
            last_scenario_description = self[key]
            if last_scenario_description.check(text_preprocessing_result, user):
                count = last_scenario_description.count
        return count
