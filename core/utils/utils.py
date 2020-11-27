# coding=utf-8
import datetime
import json
import os
import re

from collections import OrderedDict
from math import isnan, isinf
from typing import Optional
from time import time


def convert_version_to_list_of_int(version):
    if not version or re.search("[0-9]", version) is None:
        return None
    list_of_string = [re.sub("[^0-9]", "", part) for part in version.split(".")]
    list_of_int = list(map(int, list_of_string))
    return list_of_int


def subfolder_wrap(parent):
    def inner(child):
        return os.path.join(parent, child)

    return inner


def get_int(word):
    num = None
    if len(word) >= 8 and word[0] == "+":
        num = None
    else:
        try:
            num = int(word)
            if isnan(num) or isinf(num):
                num = None
        except (ValueError, OverflowError):
            num = None
    return num


def get_number(word):
    word = word.replace(',', '.')
    if "." in word or "e" in word:
        number = convert_to_float(word)
    else:
        number = get_int(word)
    return number


def convert_to_float(word: str) -> Optional[float]:
    try:
        num = float(word)
        if isnan(num) or isinf(num):
            return None
        return num
    except (ValueError, OverflowError):
        return None


def convert_to_int(x):
    ix = int(x)
    if x == ix:
        return ix
    else:
        return x


def one_of_elements_is_in_set(elements_set, set_to_check):
    if not isinstance(elements_set, set):
        elements_set = set(elements_set)
    if not isinstance(set_to_check, set):
        set_to_check = set(set_to_check)
    return elements_set.intersection(set_to_check) != set()


def all_elements_are_in_set(elements_set, set_to_check):
    if not isinstance(elements_set, set):
        elements_set = set(elements_set)
    if not isinstance(set_to_check, set):
        set_to_check = set(set_to_check)
    return len(elements_set.intersection(set_to_check)) == min(len(elements_set), len(set_to_check))


def prepare_from_one_to_many_to_one_to_one_dict(dict_one_to_many):
    dict_one_to_one = {}
    for base, synonyms in dict_one_to_many.items():
        for synonym in synonyms:
            dict_one_to_one.update({synonym: base})
    return dict_one_to_one


def merge_numbers(text):
    # пример: квартира стоит 12 345 678 рублей -> квартира стоит 12345678 рублей
    def remove_whitespace(number_match):
        return number_match.group().replace(" ", "")

    regex = re.compile("\d+(\s\d+)+")
    return regex.sub(remove_whitespace, text)


def ordered_dict(data=None):
    return OrderedDict(data)


def list_loader(data, delimiter=None):
    return data.split(delimiter)


def unixtime_to_str(unixtime):
    return datetime.datetime.fromtimestamp(int(unixtime)).strftime('%Y-%m-%d %H:%M:%S')


class HashableDict(dict):
    def __hash__(self):
        return hash(frozenset(self.items()))


def ordered_loader(coded):
    return json.loads(coded, object_pairs_hook=OrderedDict)


def current_time_ms():
    return int(round(time() * 1000))


def time_check(begin_time, reject_timeout):
    return current_time_ms() - begin_time <= reject_timeout if begin_time is not None else True
