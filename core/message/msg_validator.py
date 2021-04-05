from abc import ABC, abstractmethod


class MessageValidator(ABC):
    @abstractmethod
    def validate(self, message_name: str, payload: dict):
        raise NotImplemented()
