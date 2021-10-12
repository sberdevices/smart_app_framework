from collections import Iterable, Mapping
import re
import traceback

MASK = "***"
DEFAULT_MASKING_FIELDS = ["token", "access_token", "refresh_token", "epkId", "profileId"]
CARD_MASKING_FIELDS = ["message"]


def card_masking(record):
    card_regular = re.compile("(?:^|\s|\'|\")(?:(\d{18})|(\d{16})|(?:\d{4} ){3}(\d{4})(\s?\d{2})?)(?:$|\W)")
    d_regular = re.compile("\d")

    def sub_func(x):
        g0 = x.group(0)
        is_last_not_digit = int(g0 and not g0[-1].isdigit())
        last_char = g0[-1]

        mask = d_regular.sub("*", x.group(0))[:-(4 + is_last_not_digit)]
        digs = ((x.group(1) or '') + (x.group(2) or '') + (x.group(3) or '') + (x.group(4) or '')).replace(' ', '')[-4:]
        return mask + digs + (last_char * is_last_not_digit)

    if isinstance(record, Mapping):
        return {k: card_masking(v) for k, v in record.items()}
    elif isinstance(record, str):
        return card_regular.sub(sub_func, record)
    elif isinstance(record, Iterable):
        return [card_masking(i) for i in record]
    else:
        return record


def masking(data, masking_fields=None):
    if masking_fields is None:
        masking_fields = DEFAULT_MASKING_FIELDS
    if hasattr(data, 'items'):
        for key in data:
            if key in masking_fields:
                data[key] = MASK
            elif key in CARD_MASKING_FIELDS:
                data[key] = card_masking(data[key])
            elif isinstance(data[key], dict):
                masking(data[key], masking_fields)
            elif isinstance(data[key], list):
                for item in data[key]:
                    masking(item, masking_fields)
