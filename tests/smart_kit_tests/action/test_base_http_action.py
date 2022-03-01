import unittest
from unittest.mock import Mock, patch

from smart_kit.action.base_http import BaseHttpRequestAction


class BaseHttpRequestActionTest(unittest.TestCase):
    def setUp(self):
        self.user = Mock(parametrizer=Mock(collect=lambda *args, **kwargs: {}))

    @staticmethod
    def set_request_mock_attribute(request_mock, return_value=None):
        return_value = return_value or {}
        request_mock.return_value = Mock(
            __enter__=Mock(return_value=Mock(
                json=Mock(return_value=return_value),
                cookies={},
                headers={},
            ),),
            __exit__=Mock()
        )

    @patch('requests.request')
    def test_simple_request(self, request_mock: Mock):
        self.set_request_mock_attribute(request_mock)
        items = {
            "method": "POST",
            "url": "https://my.url.com",
        }
        result = BaseHttpRequestAction(items).run(self.user, None, {})
        request_mock.assert_called_with(url="https://my.url.com", method='POST')
        self.assertEqual(result, {})

    @patch('requests.request')
    def test_render_params(self, request_mock: Mock):
        self.set_request_mock_attribute(request_mock)
        items = {
            "method": "POST",
            "url": "https://{{url}}",
            "timeout": 3,
            "json": {
                "param": "{{value}}"
            }
        }
        params = {
            "url": "my.url.com",
            "value": "my_value"
        }
        result = BaseHttpRequestAction(items).run(self.user, None, params)
        request_mock.assert_called_with(url="https://my.url.com", method='POST', timeout=3, json={"param": "my_value"})
        self.assertEqual(result, {})

    @patch('requests.request')
    def test_headers_fix(self, request_mock):
        self.set_request_mock_attribute(request_mock)
        items = {
            "headers": {
                "header_1": 32,
                "header_2": 32.03,
                "header_3": b"d32",
                "header_4": None,
                "header_5": {"data": "value"},
            },
        }
        result = BaseHttpRequestAction(items).run(self.user, None, {})
        request_mock.assert_called_with(headers={
            "header_1": "32",
            "header_2": "32.03",
            "header_3": b"d32"
        })
        self.assertEqual(result, {})
