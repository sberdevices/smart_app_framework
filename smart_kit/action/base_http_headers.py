import json
from typing import Optional, Dict, Union, List, Any

import requests
from requests import Response
from requests.cookies import RequestsCookieJar

from core.basic_models.actions.command import Command
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult
from smart_kit.action.base_http import BaseHttpRequestAction


class BaseHttpRequestActionWithHeaders(BaseHttpRequestAction):
    def _make_response(self, request_parameters, user):
        try:
            with requests.request(**request_parameters) as response:
                response.raise_for_status()
                try:
                    data = (response.json(), response.cookies)
                except json.decoder.JSONDecodeError:
                    data = None
                self._log_response(user, response, data)
                return data
        except requests.exceptions.Timeout:
            self.error = self.TIMEOUT
        except (requests.exceptions.ConnectionError, requests.exceptions.HTTPError):
            self.error = self.CONNECTION

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[tuple[Any, RequestsCookieJar]]:
        return super().run(user, text_preprocessing_result, params)
