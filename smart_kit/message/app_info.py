from lazy import lazy

from core.names import field


class AppInfo:

    def __init__(self, value):
        self._value = value

    @lazy
    def project_id(self):
        return self._value.get(field.PROJECT_ID)

    @lazy
    def system_name(self):
        return self._value.get(field.SYSTEM_NAME)

    @lazy
    def application_id(self):
        return self._value.get(field.APPLICATION_ID)

    @lazy
    def app_version_id(self):
        return self._value.get(field.APP_VERSION_ID)

    @lazy
    def frontend_endpoint(self):
        return self._value.get(field.FRONTEND_ENDPOINT)

    @lazy
    def frontend_type(self):
        return self._value.get(field.FRONTEND_TYPE)
