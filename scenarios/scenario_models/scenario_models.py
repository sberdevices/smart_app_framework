# coding: utf-8
from collections import defaultdict

from core.model.lazy_items import LazyItems


class LoopException(Exception):
    pass


class RegisteredScenario:
    def __init__(self):
        self._values = dict()

    def __setitem__(self, key, value):
        self._values[key] = value

    def __getitem__(self, key):
        value = self._values.get(key)
        if value is None:
            value = BaseScenarioModel
        return value


scenario_models = RegisteredScenario()


def scenario_model_factory(value, description, user):
    _type = type(description)
    model = scenario_models[_type]
    return model(value, description, user)


class BaseScenarioModel:
    def __init__(self, items, description, user):
        self.description = description

    def set_break(self):
        pass

    @property
    def break_scenario(self):
        return False

    @property
    def raw(self):
        return None


class ScenarioModels(LazyItems):
    def __init__(self, items, descriptions, user):
        super(ScenarioModels, self).__init__(items, descriptions, user, scenario_model_factory)


class MetaClassifierScenarioModel(BaseScenarioModel):
    def __init__(self, value, description, user):
        super(MetaClassifierScenarioModel, self).__init__(value, description, user)
        self.scenario_id = value


class FormFillingScenarioModel(BaseScenarioModel):
    def __init__(self, value, description, user):
        super(FormFillingScenarioModel, self).__init__(value, description, user)
        self._break_scenario = False
        self._shared_data = {}
        self._postprocessing_data = list()

    def set_break(self):
        self._break_scenario = True

    def set_shared(self, key, value):
        self._shared_data[key] = value

    def get_shared(self, key):
        return self._shared_data.get(key)

    @property
    def break_scenario(self):
        return self._break_scenario

    @property
    def postprocessing_data(self):
        return self._postprocessing_data


class TreeScenarioModel(FormFillingScenarioModel):

    DEFAULT_COUNT = 10

    def __init__(self, items, description, user):
        super(TreeScenarioModel, self).__init__(items, description, user)
        items = items or {}
        self.current_node = items.get("current_node")
        self.number_of_calls = defaultdict(int)

    def add_count(self, node_id):
        self.number_of_calls[node_id] += 1
        if self.number_of_calls[node_id] == self.DEFAULT_COUNT:
            raise LoopException("the scenario is looped")

    @property
    def raw(self):
        if self.current_node:
            return {"current_node": self.current_node}
