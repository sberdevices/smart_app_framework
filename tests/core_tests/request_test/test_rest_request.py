import unittest
from unittest.mock import Mock, MagicMock

from core.request.rest_request import RestRequest


class RestRequestTest(unittest.TestCase):
    def setUp(self):
        self.expected = Mock()

    def test_get(self):
        self.rr = RestRequest({"method": "get"})
        self.rr._requests_get = MagicMock(return_value=self.expected)
        data = ["text"]
        result = self.rr.run(data)
        self.rr._requests_get.assert_called_once_with(data)
        self.assertEqual(result, self.expected)

    def test_post(self):
        self.rr = RestRequest({})
        self.rr._requests_post = MagicMock(return_value=self.expected)
        data = ["text"]
        result = self.rr.run(data)
        self.rr._requests_post.assert_called_once_with(data)
        self.assertEqual(result, self.expected)

    def test_get_disabled(self):
        self.rr = RestRequest({"method": "get", "enabled": False})
        self.rr._requests_get = MagicMock(return_value=self.expected)
        data = ["text"]
        result = self.rr.run(data)
        self.assertIsNone(result)

    def test_post_disabled(self):
        self.rr = RestRequest({"enabled": False})
        self.rr._requests_post = MagicMock(return_value=self.expected)
        data = ["text"]
        result = self.rr.run(data)
        self.assertIsNone(result)
