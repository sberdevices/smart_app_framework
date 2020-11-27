# coding: utf-8
import time
from collections import deque


class MessageHistory:
    TS = "ts"
    MESSAGE = "message"
    DIRECTION = "direction"
    INCOMING = "incoming"
    OUTGOING = "outgoing"

    def __init__(self, items, description, user):
        items = items or []
        self.items = deque(items)
        self.description = description

    def _push(self, message, direction):
        self._filter()
        stored_data = {self.TS: time.time(),
                       self.MESSAGE: message,
                       self.DIRECTION: direction}
        self.items.append(stored_data)

    def clear(self):
        self.items = deque()

    def _filter(self):
        now = time.time()
        while len(self.items) >= self.description.max_message_count:
            self.items.popleft()

        for _ in range(len(self.items)):
            threshold = self.description.lifetime + self.items[0].get(self.TS)
            if now > threshold:
                self.items.popleft()
            else:
                break

    @property
    def raw(self):
        return list(self.items)
