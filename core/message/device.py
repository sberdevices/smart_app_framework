from lazy import lazy


class Device:

    def __init__(self, value):
        self._value = value

    @lazy
    def value(self):
        return self._value

    @lazy
    def platform_type(self):
        return self._value.get("platformType") or ""

    @lazy
    def platform_version(self):
        return self._value.get("platformVersion") or ""

    @lazy
    def surface(self):
        return self._value.get("surface") or ""

    @lazy
    def surface_version(self):
        return self._value.get("surfaceVersion") or ""

    @lazy
    def features(self):
        return self._value.get("features") or {}

    @lazy
    def capabilities(self):
        return self._value.get("capabilities") or {}

    @lazy
    def additional_info(self):
        return self._value.get("additionalInfo") or {}

    @lazy
    def tenant(self):
        return self._value.get("tenant") or ""

    @lazy
    def device_id(self):
        return self._value.get("deviceId") or ""
