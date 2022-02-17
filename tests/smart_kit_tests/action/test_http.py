import unittest
from unittest.mock import Mock, patch

from smart_kit.action.http import HTTPRequestAction
from tests.smart_kit_tests.action.test_base_http_action import BaseHttpRequestActionTest


class HttpRequestActionTest(unittest.TestCase):
    def setUp(self):
        self.user = Mock(
            parametrizer=Mock(collect=lambda *args, **kwargs: {}),
            descriptions={
                "behaviors": {
                    "my_behavior": Mock(timeout=Mock(return_value=3))
                }
            }
        )

    @patch('requests.request')
    def test_simple_request(self, request_mock: Mock):
        BaseHttpRequestActionTest.set_request_mock_attribute(request_mock, return_value={'data': 'value'})
        items = {
            "params": {
                "method": "POST",
                "url": "https://my.url.com",
            },
            "store": "user_variable",
            "behavior": "my_behavior",
        }
        HTTPRequestAction(items).run(self.user, None, {})
        request_mock.assert_called_with(url="https://my.url.com", method='POST', timeout=3)
        self.assertTrue(self.user.descriptions["behaviors"]["my_behavior"].success_action.run.called)
        self.assertTrue(self.user.variables.set.called)
        self.user.variables.set.assert_called_with("user_variable", {'data': 'value'})
