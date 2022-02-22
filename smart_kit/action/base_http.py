import json
from typing import Optional, Dict, Union, List, Any

import requests

import core.logging.logger_constants as log_const
from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import NodeAction
from core.logging.logger_utils import log
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

    def _make_response(self, request_parameters, user):
        try:
            with requests.request(**request_parameters) as response:
                response.raise_for_status()
                try:
                    data = response.json()
                except json.decoder.JSONDecodeError:
                    data = None
                self._log_response(user, response, data)
                return data
        except requests.exceptions.Timeout:
            self.error = self.TIMEOUT
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
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

    def _log_response(self, user, response, data, additional_params=None):
        additional_params = additional_params or {}
        log(f"{self.__class__.__name__}.run get https response ", user=user, params={
            'headers': dict(response.headers),
            'time': response.elapsed.microseconds,
            'cookie': {i.name: i.value for i in response.cookies},
            'status': response.status_code,
            'data': data,
            log_const.KEY_NAME: "got_http_response",
            **additional_params,
        })

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        params = params or {}
        request_parameters = self._get_request_params(user, text_preprocessing_result, params)
        self._log_request(user, request_parameters)
        return self._make_response(request_parameters, user)
