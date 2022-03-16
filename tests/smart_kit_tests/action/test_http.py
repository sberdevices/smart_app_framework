import unittest
from unittest.mock import Mock, patch

from smart_kit.action.http import HTTPRequestAction


class HttpRequestActionTest(unittest.TestCase):
    TIMEOUT = 4

    def setUp(self):
        self.user = Mock(
            parametrizer=Mock(collect=lambda *args, **kwargs: {}),
            descriptions={
                "behaviors": {
                    "my_behavior": Mock(timeout=Mock(return_value=self.TIMEOUT))
                }
            }
        )

    def set_request_mock_attribute(self, request_mock, return_value=None):
        return_value = return_value or {}
        request_mock.return_value = Mock(
            __enter__=Mock(return_value=Mock(
                json=Mock(return_value=return_value),
                cookies={},
                headers={},
            ), ),
            __exit__=Mock()
        )

    @patch('requests.request')
    def test_simple_request(self, request_mock: Mock):
        self.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        items = {
            "params": {
                "method": "POST",
                "url": "https://my.url.com",
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        HTTPRequestAction(items).run(self.user, None, {})
        request_mock.assert_called_with(url="https://my.url.com", method='POST', timeout=self.TIMEOUT)
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("user_variable", {'data': 'value'})

    @patch('requests.request')
    def test_render_params(self, request_mock: Mock):
        self.set_request_mock_attribute(request_mock)
        items = {
            "params": {
                "method": "POST",
                "url": "https://{{url}}",
                "timeout": 3,
                "json": {
                    "param": "{{value}}"
                }
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        params = {
            "url": "my.url.com",
            "value": "my_value"
        }
        HTTPRequestAction(items).run(self.user, None, params)
        request_mock.assert_called_with(url="https://my.url.com", method='POST', timeout=3, json={"param": "my_value"})

    @patch('requests.request')
    def test_headers_fix(self, request_mock):
        self.set_request_mock_attribute(request_mock)
        items = {
            "params": {
                "headers": {
                    "header_1": 32,
                    "header_2": 32.03,
                    "header_3": b"d32",
                    "header_4": None,
                    "header_5": {"data": "value"},
                },
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        HTTPRequestAction(items).run(self.user, None, {})
        request_mock.assert_called_with(headers={
            "header_1": "32",
            "header_2": "32.03",
            "header_3": b"d32"
        }, method=HTTPRequestAction.DEFAULT_METHOD, timeout=self.TIMEOUT)

    @patch('requests.request')
    def test_beheivor_is_none(self, request_mock):
        self.set_request_mock_attribute(request_mock)
        items = {
            "params": {
            },
            "store": "user_variable",
        }
        HTTPRequestAction(items).run(self.user, None, {})
        request_mock.assert_called_with(method=HTTPRequestAction.DEFAULT_METHOD,
                                        timeout=HTTPRequestAction.DEFAULT_TIMEOUT)
