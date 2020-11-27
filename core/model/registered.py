# coding: utf-8


class Registered(dict):

    def __getitem__(self, key):
        value = self.get(key, key)
        assert not isinstance(value, str), "{} factory is not registered".format(key)
        return value


registered_factories = Registered()
