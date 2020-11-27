from collections import Iterable, Mapping
import re


class LogMasker:
    """
    Regular expression is used to find 16 digit or 18 digit number that could be
    between single or double quotes
    and any non digit character
    """
    card_regular = re.compile("(?:^|\s|\'|\")(?:(\d{18})|(\d{16})|(?:\d{4} ){3}(\d{4})(\s?\d{2})?)(?:$|\D)")
    d_regular = re.compile("\d")

    @classmethod
    def _card_sub_func(cls, x):
        g0 = x.group(0)

        is_last_not_digit = int(g0 and not g0[-1].isdigit())
        last_char = g0[-1]

        mask = cls.d_regular.sub("*", x.group(0))[:-(4 + is_last_not_digit)]
        digs = ((x.group(1) or '') + (x.group(2) or '') + (x.group(3) or '') + (x.group(4) or '')).replace(' ', '')[-4:]
        return mask + digs + (last_char * is_last_not_digit)

    @classmethod
    def mask_structure(cls, record, func):
        if isinstance(record, Mapping):
            return {k: cls.mask_structure(v, func) for k, v in record.items()}
        elif isinstance(record, str):
            return func(record)
        elif isinstance(record, Iterable):
            return [cls.mask_structure(i, func) for i in record]
        else:
            return record

    @classmethod
    def regular_exp(cls, record):
        return cls.card_regular.sub(cls._card_sub_func, record)

    @classmethod
    def percent_fix(cls, record):
        return str(record).replace("%", "%%")
