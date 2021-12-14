from typing import Callable, Optional, Iterable, Mapping, Union, Pattern, Match, MutableMapping
import re

MASK = "***"
DEFAULT_MASKING_FIELDS = ["token", "access_token", "refresh_token", "epkId", "profileId"]
CARD_MASKING_FIELDS = ["message", "debug_info", "normalizedMessage", "incoming_text", "annotations"]

card_regular = re.compile(r"(?:(\d{18})|(\d{16})|(?:\d{4} ){3}(\d{4})(\s?\d{2})?)")


class Counter(object):
    def __init__(self):
        self.items = 0
        self.collections = 0
        self.max_depth = 1


def luhn_checksum(card_number: str) -> bool:
    digits = [int(d) for d in card_number]
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits) + sum(map(lambda x: (x * 2) % 10 + (x * 2) // 10, even_digits))
    return checksum % 10 == 0


def card_sub_func(x: Match[str]) -> str:
    d_regular = re.compile(r"\d")

    g0 = x.group(0)
    is_last_not_digit = int(g0 and not g0[-1].isdigit())
    last_char = g0[-1]

    mask = d_regular.sub("*", x.group(0))[:-(4 + is_last_not_digit)]
    digs = (x.group(0) or '').replace(' ', '')[-4:]
    return mask + digs + (last_char * is_last_not_digit)


def check_value_is_collection(value):
    return isinstance(value, MutableMapping) or isinstance(value, Iterable) and not isinstance(value, str)


def masking(data: Union[MutableMapping, Iterable], masking_fields: Optional[Union[MutableMapping, Iterable]] = None,
            deep_level: int = 2, mask_available_depth: int = -1, masking_on: bool = False,
            card_masking_on: bool = False):
    """
    :param data: коллекция для маскирования приватных данных
    :param masking_fields: поля для обязательной маскировки независимо от уровня
    :param deep_level: глубина сохранения структуры маскируемого поля
    :param mask_available_depth: глубина глубокой маскировки полей без сохранения структуры (см ниже)
    :param masking_on: флаг о включенной выше маскировке, в случае маскировки вложенных полей
    :param card_masking_on: флаг о вкюченном маскировании карт
    """
    if masking_fields is None:
        masking_fields = DEFAULT_MASKING_FIELDS

    if isinstance(masking_fields, Iterable):
        masking_fields = {key: deep_level for key in masking_fields}

    # тут в зависимости от листа или словаря создаем итератор
    if isinstance(data, MutableMapping):
        key_gen = data.items()
    else:
        key_gen = enumerate(data)

    for key, _ in key_gen:
        value_is_collection = check_value_is_collection(data[key])
        if masking_on or key in masking_fields:
            if value_is_collection:
                # если глубина не превышена, идем внутрь с включенным флагом и уменьшаем глубину
                if masking_on and deep_level > 0:
                    masking(data[key], masking_fields, deep_level - 1, masking_on=True)
                elif key in masking_fields and masking_fields[key] > 0:
                    masking(data[key], masking_fields, masking_fields[key], masking_on=True)
                else:
                    counter = deep_mask(data[key], depth=1, available_depth=mask_available_depth)
                    data[
                        key] = f'*items-{counter.items}*collections-{counter.collections}*maxdepth-{counter.max_depth}*'
            elif data[key] is not None:  # в случае простого элемента. маскируем как ***
                data[key] = '***'
        elif card_masking_on and isinstance(data[key], str):  # проверка на реквизиты карты
            data[key] = card_regular.sub(card_sub_func, data[key])
        elif key in CARD_MASKING_FIELDS:  # проверка на реквизиты карты
            masking(data[key], masking_fields, deep_level, masking_on=masking_on, card_masking_on=True)
        elif value_is_collection:
            # если маскировка не нужна уходим глубже без включенного флага
            masking(data[key], masking_fields, deep_level, masking_on=False, card_masking_on=card_masking_on)


def deep_mask(data: Union[MutableMapping, Iterable], depth: int, available_depth: int = -1,
              counter: Optional[Counter] = None):
    """
    Функция глубокой максировки для вложенной структуры, tuple из 3х чисел:
     1 - количество простых элементов,
     2 - количество коллекций,
     3 - максимальную глубину

    :param counter: объект счетчик
    :param available_depth: максимальная глубина прохода, при -1 глубина не ограничена
    :param data: структура маскируемая без сохранения структуры
    :param depth: текущая глубина вложенности

    """
    # в зависимости от листа или словаря создаем итератор
    if isinstance(data, MutableMapping):
        key_gen = data.items()
    else:
        key_gen = enumerate(data)

    if counter is None:
        counter = Counter()

    for key, _ in key_gen:
        if check_value_is_collection(data[key]):
            counter.collections += 1
            # если встречаем коллекцию и глубина не превышена идем внутрь
            if depth < available_depth or depth == -1:
                deep_mask(data[key], depth + 1, available_depth, counter)
        else:
            # если элемент простой крутим счетчик простых элементов
            counter.items += 1
            if depth > counter.max_depth:
                counter.max_depth = depth

    return counter
