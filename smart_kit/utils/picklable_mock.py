from unittest.mock import Mock, MagicMock


class PicklableMock(Mock):
    def __reduce__(self):
        return Mock, ()


class PicklableMagicMock(MagicMock):
    def __reduce__(self):
        return MagicMock, ()
