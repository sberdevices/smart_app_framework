# coding: utf-8


class PreprocessingMessagesDescription:
    def __init__(self, items):
        items = items or {}
        self.max_message_count = items["messages"]
        self.lifetime = items["lifetime"]
