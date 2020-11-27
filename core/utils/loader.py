# coding=utf-8
from collections import OrderedDict

import json


def ordered_json(data):
    return json.loads(data, object_pairs_hook=OrderedDict)


def reverse_json_dict(data):
    data = json.loads(data)
    result = dict()
    for key, values in data.items():
        for value in values:
            result[value] = key
    return result
