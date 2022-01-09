from unittest.mock import Mock


class PicklableMock(Mock):
    def __reduce__(self):
        return Mock, ()
