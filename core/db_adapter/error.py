from core.db_adapter.db_adapter import DBAdapterException


class NotSupportedOperation(DBAdapterException):
    def __init__(self, msg=None):
        msg = msg or "Operation is not supported"
        super().__init__(msg)
