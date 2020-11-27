from typing import Optional, Dict, Any, Union

from core.text_preprocessing.base import BaseTextPreprocessingResult

from core.unified_template.unified_template import UnifiedTemplate

from core.model.base_user import BaseUser

from core.basic_models.parametrizers.parametrizer import BasicParametrizer
import collections
import json
from jinja2 import exceptions as jexcept

from core.basic_models.actions.basic_actions import Action


class SetVariableAction(Action):
    version: Optional[int]
    parametrizer: BasicParametrizer
    loader: Optional[str]
    key: str
    loader: Optional[str]
    loaders = collections.defaultdict(str, {"json": json.loads, "float": float, "int": int})
    ttl: int
    value: Union[str, Dict]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(SetVariableAction, self).__init__(items, id)
        self.key: str = items["key"]
        self.loader = items.get('loader')
        self.ttl: int = items.get("ttl")
        value: str = items["value"]
        self.template: UnifiedTemplate = UnifiedTemplate(value)

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        params = user.parametrizer.collect(text_preprocessing_result)
        try:
            # if path is wrong, it may fail with UndefinedError
            # notion: {key: None} will return "None";
            # not existing key or value "" will return ""; otherwise question in scenario will go in cycles
            value = self.template.render(params)
        except jexcept.UndefinedError:
            value = None

        if self.loader:
            if value:
                loader = self.loaders[self.loader]
                value = loader(value)
            else:
                value = None

        user.variables.set(self.key, value, self.ttl)


class DeleteVariableAction(Action):
    version: Optional[int]
    key: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(DeleteVariableAction, self).__init__(items, id)
        self.key: str = items["key"]

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        user.variables.delete(self.key)


class ClearVariablesAction(Action):
    version: Optional[int]

    def __init__(self, items: Dict[str, Any] = None, id: Optional[str] = None):
        super(ClearVariablesAction, self).__init__(items, id)

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        user.variables.clear()
