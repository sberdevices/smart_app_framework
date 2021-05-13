import requests

from typing import Optional, Dict, Union, List, Any

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import NodeAction
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult


class HTTPRequestAction(NodeAction):
    def __init__(self, items, id=None):
        super().__init__(items, id)
        self.params = items["params"]
        self.url = self.params["url"]
        self.method = self.params["method"]
        self.store = items["store"]
        self.behavior = items["behavior"]

    @staticmethod
    def _check_headers_validity(headers: Dict[str, Any]) -> Dict[str, str]:
        for header_name, header_value in headers.items():
            if not isinstance(header_value, str) or not isinstance(header_value, bytes):
                headers[header_name] = str(header_value)
        return headers

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        behavior_description = user.descriptions["behaviors"][self.behavior]

        request_params = self.params
        request_params["timeout"] = behavior_description.timeout(user)

        params = params or {}
        collected = user.parametrizer.collect(text_preprocessing_result)
        params.update(collected)

        request_parameters = self._get_rendered_tree_recursive(self._get_template_tree(request_params), params)

        req_headers = request_parameters.get("headers")
        if req_headers:
            # Заголовки в запросах должны иметь тип str или bytes. Поэтому добавлена проверка и приведение к типу str,
            # на тот случай если в сценарии заголовок указали как int, float и тд
            request_parameters["headers"] = self._check_headers_validity(req_headers)

        try:
            with requests.request(**request_parameters) as response:
                response.raise_for_status()
                user.variables.set(self.store, response.json())
                return behavior_description.success_action.run(user, text_preprocessing_result, None)
        except requests.exceptions.Timeout:
            return behavior_description.timeout_action.run(user, text_preprocessing_result, None)
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            return behavior_description.fail_action.run(user, text_preprocessing_result, None)
