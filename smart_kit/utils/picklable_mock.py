from unittest.mock import Mock, MagicMock, AsyncMock


class PicklableMock(Mock):
    def __reduce__(self):
        return Mock, ()


class AsyncPicklableMock(AsyncMock):
    def __reduce__(self):
        return AsyncMock, ()


class PicklableMagicMock(MagicMock):
    def __reduce__(self):
        return MagicMock, ()
