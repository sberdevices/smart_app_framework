# coding: utf-8
from scenarios.user.message_history.message_history import MessageHistory


class PreprocessingScenariosMessages(MessageHistory):

    def add(self, text_preprocessing_result):
        if text_preprocessing_result is not None and text_preprocessing_result.original_text:
            self._push(text_preprocessing_result.raw, self.INCOMING)

    @property
    def processed_items(self):
        return [item['message'] for item in reversed(self.items)]
