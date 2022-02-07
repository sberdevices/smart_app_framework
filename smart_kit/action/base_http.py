import requests
import aiohttp

from typing import Optional, Dict, Union, List, Any

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import NodeAction
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult


class BaseHttpRequestAction(NodeAction):
    """
    Example:
        {
            // обязательные параметры
            "method": "POST",
            "url": "http://some_url.com/...",

            // необязательные параметры
            "json": {
                "data": "value",
                ...
            },
            "timeout": 120,
            "headers": {
                "Content-Type":"application/json"
            }
        }
    """
    POST = "POST"
    GET = "GET"
    DEFAULT_METHOD = POST

    TIMEOUT = "TIMEOUT"
    CONNECTION = "CONNECTION"

    def __init__(self, items, id=None):
        super().__init__(items, id)
        self.method_params = items
        self.error = None

    @staticmethod
    def _check_headers_validity(headers: Dict[str, Any]) -> Dict[str, str]:
        for header_name, header_value in headers.items():
            if not isinstance(header_value, str) or not isinstance(header_value, bytes):
                headers[header_name] = str(header_value)
        return headers

    def _make_response(self, request_parameters):
        try:
            with requests.request(**request_parameters) as response:
                response.raise_for_status()
                return response.json()
        except requests.exceptions.Timeout:
            self.error = self.TIMEOUT
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            self.error = self.CONNECTION

    def _get_requst_params(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None):
        collected = user.parametrizer.collect(text_preprocessing_result)
        params.update(collected)

        request_parameters = self._get_rendered_tree_recursive(self._get_template_tree(self.method_params), params)

        req_headers = request_parameters.get("headers")
        if req_headers:
            # Заголовки в запросах должны иметь тип str или bytes. Поэтому добавлена проверка и приведение к типу str,
            # на тот случай если в сценарии заголовок указали как int, float и тд
            request_parameters["headers"] = self._check_headers_validity(req_headers)
        return request_parameters

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        params = params or {}
        request_parameters = self._get_requst_params(user, text_preprocessing_result, params)
        return self._make_response(request_parameters)


class AsyncBaseHttpRequestAction(BaseHttpRequestAction):

    async def _make_response(self, request_parameters):
        try:
            async with aiohttp.request(**request_parameters) as resp:
                return await resp.json()
        except (aiohttp.ClientTimeout, aiohttp.ServerTimeoutError):
            self.error = self.TIMEOUT
        except aiohttp.ClientError:
            self.error = self.CONNECTION

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                  params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        params = params or {}
        request_parameters = self._get_requst_params(user, text_preprocessing_result, params)
        return await self._make_response(request_parameters)

