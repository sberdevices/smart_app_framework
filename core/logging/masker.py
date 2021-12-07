from collections import Iterable, Mapping
import re
from smart_kit.utils.pickle_copy import pickle_deepcopy

from core.utils.masking_message import masking

class LogMasker:
    """
    DEPRECATED: Card masks in core/utils/masking_message.py

    Regular expression is used to find 16 digit or 18 digit number that could be
    between single or double quotes
    and any non digit character
    """

    @classmethod
    def _card_sub_func(cls, x):
        return x

    @classmethod
    def mask_structure(cls, record, func):
        r = pickle_deepcopy(record)
        masking(r)
        return r

    @classmethod
    def regular_exp(cls, record):
        return record

    @classmethod
    def percent_fix(cls, record):
        return str(record).replace("%", "%%")
