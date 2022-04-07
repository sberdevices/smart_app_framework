import asyncio
from typing import Optional, Dict, Union, List, Any

import aiohttp
import aiohttp.client_exceptions
from aiohttp import ClientTimeout

import core.logging.logger_constants as log_const
from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import NodeAction
from core.logging.logger_utils import log
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult


class HTTPRequestAction(NodeAction):
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

    POST = "POST"
    GET = "GET"
    DEFAULT_METHOD = POST

    TIMEOUT = "TIMEOUT"
    CONNECTION = "CONNECTION"

    def __init__(self, items, id=None):
        super().__init__(items, id)
        self.method_params = items['params']
        self.method_params.setdefault("method", self.DEFAULT_METHOD)
        self.error = None
        self.init_save_params(items)

    def init_save_params(self, items):
        self.store = items["store"]
        self.behavior = items.get("behavior")

    def preprocess(self, user, text_processing, params):
        behavior_description = user.descriptions["behaviors"][self.behavior]
        self.method_params.setdefault("timeout", behavior_description.timeout(user))
        self.method_params["timeout"] = ClientTimeout(self.method_params["timeout"])

    @staticmethod
    def _check_headers_validity(headers: Dict[str, Any], user) -> Dict[str, str]:
        for header_name, header_value in list(headers.items()):
            if not isinstance(header_value, (str, bytes)):
                if isinstance(header_value, (int, float, bool)):
                    headers[header_name] = str(header_value)
                else:
                    log(f"{__class__.__name__}._check_headers_validity remove header {header_name} because "
                        f"({type(header_value)}) is not in [int, float, bool, str, bytes]", user=user, params={
                        log_const.KEY_NAME: "sent_http_remove_header",
                    })
                    del headers[header_name]
        return headers

    async def _make_response(self, request_parameters, user):
        try:
            async with aiohttp.request(**request_parameters) as response:
                response.raise_for_status()
                self._log_response(user, response)
                return response
        except (aiohttp.ServerTimeoutError, asyncio.TimeoutError):
            self.error = self.TIMEOUT
        except aiohttp.ClientError:
            self.error = self.CONNECTION

    def _get_request_params(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
                            params: Optional[Dict[str, Union[str, float, int]]] = None):
        collected = user.parametrizer.collect(text_preprocessing_result)
        params.update(collected)
        request_parameters = self._get_rendered_tree_recursive(self._get_template_tree(self.method_params), params)
        req_headers = request_parameters.get("headers")
        if req_headers:
            # Заголовки в запросах должны иметь тип str или bytes. Поэтому добавлена проверка и приведение к типу str,
            # на тот случай если в сценарии заголовок указали как int, float и тд
            request_parameters["headers"] = self._check_headers_validity(req_headers, user)
        return request_parameters

    def _log_request(self, user, request_parameters, additional_params=None):
        additional_params = additional_params or {}
        log(f"{self.__class__.__name__}.run sent https request ", user=user, params={
            **request_parameters,
            log_const.KEY_NAME: "sent_http_request",
            **additional_params,
        })

    def _log_response(self, user, response, additional_params=None):
        additional_params = additional_params or {}
        log(f"{self.__class__.__name__}.run get https response ", user=user, params={
            'headers': dict(response.headers),
            'cookie': {k: v.value for k, v in response.cookies.items()},
            'status': response.status,
            log_const.KEY_NAME: "got_http_response",
            **additional_params,
        })

    async def process_result(self, response, user, text_preprocessing_result, params):
        behavior_description = user.descriptions["behaviors"][self.behavior] if self.behavior else None
        action = None
        if self.error is None:
            try:
                data = await response.json()
            except aiohttp.client_exceptions.ContentTypeError:
                data = None
            user.variables.set(self.store, data)
            action = behavior_description.success_action if behavior_description else None
        elif behavior_description is not None:
            if self.error == self.TIMEOUT:
                action = behavior_description.timeout_action
            else:
                action = behavior_description.fail_action
        if action:
            return await action.run(user, text_preprocessing_result, None)

    async def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self.preprocess(user, text_preprocessing_result, params)
        params = params or {}
        request_parameters = self._get_request_params(user, text_preprocessing_result, params)
        self._log_request(user, request_parameters)
        response = await self._make_response(request_parameters, user)
        return await self.process_result(response, user, text_preprocessing_result, params)
