from typing import Optional, Dict, Union, List

from core.basic_models.actions.basic_actions import Action
from core.basic_models.actions.command import Command
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult
from smart_kit.action.base_http import BaseHttpRequestAction


class HTTPRequestAction(Action):
    """
    Example:
        {
            "params": {
                "method": "POST",
                "url": "https://some_url.com/...",
                ... (см. BaseHttpRequestAction)
            },
            "store": "..."  // название переменной в user.variables, куда сохранится результат
            "behavior": "..."  // название behavior'a, вызываемого после исполнения запроса
        }
    """

    HTTP_ACTION = BaseHttpRequestAction

    def __init__(self, items, id=None):
        self.http_action = self.HTTP_ACTION(items["params"], id)
        self.store = items["store"]
        self.behavior = items["behavior"]
        super().__init__(items, id)

    def preprocess(self, user, text_processing, params):
        behavior_description = user.descriptions["behaviors"][self.behavior]
        self.http_action.method_params.setdefault("timeout", behavior_description.timeout(user))

    def process_result(self, result, user, text_preprocessing_result, params):
        behavior_description = user.descriptions["behaviors"][self.behavior]
        if self.http_action.error is None:
            user.variables.set(self.store, result)
            action = behavior_description.success_action
        elif self.http_action.error == self.http_action.TIMEOUT:
            action = behavior_description.timeout_action
        else:
            action = behavior_description.fail_action
        return action.run(user, text_preprocessing_result, None)

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self.preprocess(user, text_preprocessing_result, params)
        result = self.http_action.run(user, text_preprocessing_result, params)
        return self.process_result(result, user, text_preprocessing_result, params)
