import json
from typing import Dict, Union

import yaml
from attr import dataclass


@dataclass(slots=True)
class FeatureToggles:
    _toggles: Dict[str, bool]

    def is_enabled(self, toggle_name: str) -> bool:
        return self._toggles[toggle_name]

    def has_toggle(self, toggle_name: str) -> bool:
        return toggle_name in self._toggles

    def update(self, toggles: Dict[str, bool]):
        self._toggles.update(toggles)


def get_feature_toggles(input_params: Union[str, Dict[str, bool]]) -> FeatureToggles:
    """Функция может принимать на вход как словарь с toggles, так и конфиг (строковый путь к нему)
    в формете .json или .yml, где хранятся toggles.
    Возвращает объект FeatureToggles с загруженными toggles.
    """
    if isinstance(input_params, dict):
        toggles = input_params
    elif isinstance(input_params, str):
        if ".json" in input_params:
            with open(input_params, "r") as jsonfile:
                toggles = json.load(jsonfile)
        elif ".yml" in input_params:
            with open(input_params, "r") as ymlfile:
                toggles = yaml.load(ymlfile)
        else:
            raise Exception("Not supported file type, it should be .json or .yml!")
    else:
        raise Exception(f"Not supported type for input: {type(input_params)}, "
                        f"it should be string consists path to toggles config or dict with toggles!")
    return FeatureToggles(toggles)
