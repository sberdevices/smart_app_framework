import types


def to_bool(value):
    if str(value).lower() == "true":
        return True

    if str(value).lower() == "false":
        return False

    if str(value).isdigit():
        value = int(value)

    return bool(value)


def as_is(value):
    return value


__typecast_map = {
    bool: to_bool,
    float: float,
    int: int,
    str: str,
}

TYPECAST_MAP = types.MappingProxyType(__typecast_map)