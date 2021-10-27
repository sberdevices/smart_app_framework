from typing import Callable, Optional, Iterable, Mapping, Union, Pattern, Match, MutableMapping
import re

MASK = "***"
DEFAULT_MASKING_FIELDS = ["token", "access_token", "refresh_token", "epkId", "profileId"]
CARD_MASKING_FIELDS = ["message"]

card_regular = re.compile("(?:(\d{18})|(\d{16})|(?:\d{4} ){3}(\d{4})(\s?\d{2})?)")


def luhn_checksum(card_number: str) -> bool:
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits) + sum(map(lambda x: (x * 2) % 10 + (x * 2) // 10, even_digits))
    return checksum % 10 == 0


def card_sub_func(x: Match[str]) -> str:
    d_regular = re.compile("\d")

    g0 = x.group(0)
    is_last_not_digit = int(g0 and not g0[-1].isdigit())
    last_char = g0[-1]

    mask = d_regular.sub("*", x.group(0))[:-(4 + is_last_not_digit)]
    digs = (x.group(0) or '').replace(' ', '')[-4:]
    return mask + digs + (last_char * is_last_not_digit)


def regex_masking(record: Union[Mapping, str, Iterable], regex: Pattern[str], func: Callable[[Match[str]], str]) \
        -> Union[Mapping, str, Iterable]:
    if isinstance(record, Mapping):
        return {k: regex_masking(v, regex, func) for k, v in record.items()}
    elif isinstance(record, str):
        return regex.sub(func, record)
    elif isinstance(record, Iterable):
        return [regex_masking(i, regex, func) for i in record]
    else:
        return record


def masking(data: MutableMapping, masking_fields: Optional[Iterable] = None):
    if masking_fields is None:
        masking_fields = DEFAULT_MASKING_FIELDS
    if isinstance(data, MutableMapping):
        for key in data:
            if key in masking_fields:
                data[key] = MASK
            elif key in CARD_MASKING_FIELDS:
                data[key] = regex_masking(data[key], card_regular, card_sub_func)
            elif isinstance(data[key], str):
                pass
            elif isinstance(data[key], MutableMapping):
                masking(data[key], masking_fields)
            elif isinstance(data[key], Iterable):
                for item in data[key]:
                    masking(item, masking_fields)
