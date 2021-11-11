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


def masking(data: Union[MutableMapping, Iterable], masking_fields: Optional[Iterable] = None, masking_on: bool = False, deep_info: int = 2, mask_available_depth: int = -1):
    """
    :param masking_on: флаг о включенной выше маскировке, в случае маскировки вложенных полей
    :param deep_info: глубина сохранения структуры маскируемого поля
    :param mask_available_depth: глубина глубокой маскировки полей без сохранения структуры (см ниже)
    """
    if masking_fields is None:
        masking_fields = DEFAULT_MASKING_FIELDS

    if isinstance(data, MutableMapping):  # тут в зависимости от листа или словаря создаем итератор
        key_gen = data.items()
        is_dict = True
    else:
        key_gen = enumerate(data)
        is_dict = False

    for key, _ in key_gen:
        if (is_dict and key in masking_fields) or masking_on:  # пероверям, либо мы уже выше имеем включенный флаг маскировки либо мы встретили ключ в словаре для маскировки
            if isinstance(data[key], MutableMapping) or isinstance(data[key], Iterable):  # проверяем наш элемент, является ли он словарем или списком
                if deep_info:
                    masking(data[key], masking_fields, True, deep_info - 1)  # если глубина не превышена, идем внутрь с включенным флагом и уменьшаем глубину
                else:
                    item_counter, collection_counter, max_depth = deep_mask(data[key], item_counter=[0,],collection_counter=[0,],
                                                                                 max_depth=[1,], depth=1, available_depth=mask_available_depth)  # если глубина превышена маскируем составной маской
                    data[key] = '*{}*{}*{}*'.format(item_counter, collection_counter, max_depth)
            elif data[key] is not None:  # в случае простого элемента. маскируем как ***
                data[key] = '***'
        elif key in CARD_MASKING_FIELDS:  # проверка на реквизиты карты
            data[key] = regex_masking(data[key], card_regular, card_sub_func)
        elif isinstance(data[key], MutableMapping) or isinstance(data[key], Iterable):  # если маскировка не нужна уходим глубже без включенного флага
            masking(data[key], masking_fields, False, deep_info)


def deep_mask(data: Union[MutableMapping, Iterable] , item_counter: Iterable, collection_counter: Iterable, max_depth: Iterable,
              depth: int, available_depth: int = -1):
    """
    Функция глубокой максировки для вложенной структуры, возвращает 3 числа через *, 1 - количество простых элементов,
    2 - количество коллекций, 3 - максимальную глубину
    :param item_counter, collection_counter, max_depth - счетчики
    :param depth: текущая глубина вложенности
    :param available_depth: максимальная допустимая глубина, -1 неограниченная
    """
    if depth > max_depth[0]:  # проверяем максимальную глубину
        max_depth[0] = depth

    if isinstance(data, MutableMapping):  # в зависимости от листа или словаря создаем итератор
        key_gen = data.items()
    else:
        key_gen = enumerate(data)

    for key, _ in key_gen:
        if isinstance(data[key], MutableMapping) or isinstance(data[key], Iterable):
            collection_counter[0] += 1  # если встречаем коллекцию крутим счетчик коллекций и если глубина не превышена идем внутрь
            if available_depth > depth or available_depth == -1:
                deep_mask(data[key],item_counter, collection_counter, max_depth, depth+1, available_depth)
        else:  # если элемент простой крутим счетчик простых элементов
            item_counter[0] += 1

    return item_counter[0], collection_counter[0], max_depth[0]

"""
example 
structure = {'token': [12,     12,   {'key': [12, 12]}],  'notoken': [12,{'token':12}]}
after masking
structure = {'token': ['***', '***', {'key': '*2*0*1*'}], 'notoken': [12, {'token': '***'}]}
"""
