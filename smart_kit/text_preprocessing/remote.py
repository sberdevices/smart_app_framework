import requests
import json


class BaseTextNormalizer:
    def __init__(self, text, context=None, message_type="text"):
        self.text = text
        self.context = context or []
        self.message_type = message_type

    @classmethod
    def normalize(cls, original_text, *args, **kwargs):
        inst = cls(text=original_text)
        return inst.get_result(*args, **kwargs)

    def get_result(self, *args, **kwargs):
        raise NotImplementedError


class HTTPTextNormalizer(BaseTextNormalizer):

    def get_result(self, address):
        response = self._get_response(address)
        return json.loads(response.text, encoding=response.encoding)

    def _get_response(self, address):
        response = requests.get(address, params={"original_text": self.text})
        response.raise_for_status()
        return response
