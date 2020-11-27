import heapq


class HeapqKV:
    def __init__(self, value_to_key_func):
        self._heapq = []
        self._to_remove = set()
        self._value_to_key = value_to_key_func

    def value_to_key(self, value):
        return self._value_to_key(value)

    def push(self, key, value):
        heapq.heappush(self._heapq, (key, value))

    def get_head_key(self):
        while self._heapq:
            top = self._heapq[0]
            if self._check_key_valid(top[1]):
                return top[0]
            else:
                heapq.heappop(self._heapq)

    def pop(self):
        while self._heapq:
            top = self._heapq[0]
            if self._check_key_valid(top[1]):
                return heapq.heappop(self._heapq)
            else:
                heapq.heappop(self._heapq)

    def remove(self, key):
        self._to_remove.add(key)

    def _check_key_valid(self, value):
        key = self.value_to_key(value)
        if key in self._to_remove:
            self._to_remove.remove(key)
            return False
        return True



