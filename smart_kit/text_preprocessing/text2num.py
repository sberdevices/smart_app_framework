import re

from core.text_preprocessing.grammem.grammem_constants import LEMMA, TEXT, TOKEN_TYPE, TOKEN_VALUE, VALUE, \
    LIST_OF_TOKEN_TYPES_DATA, ADJECTIVAL_NUMBER
from core.utils.utils import get_number

NUM_TOKEN = "NUM_TOKEN"

KILO_PREFIX = "к"
NUMBER_POS = 1
TOKEN_POS = 0
NOT_FROM_DICTIONARY_POS = 2
META_TOKEN_POS = 3
BEZ_POS = 4
ADJECTIVAL_POS = 5
NUMBER = "номер"
ADPOSITIONS = ["с", "от"]
BEZ_LIST = ["без", "Без"]
HOURS_RANGE = range(0, 21)
BEG_LIST = ["два", "три", "четыре"]


class Text2Num:
    """
    Класс предназначен для нахождения чисел в тексте и ковертации их в запись цифрами
    с приписыванием типа токена NUM_TOKEN
    """
    BLACK_LIST = set(range(10, 20))

    def __init__(self, text2num_dict_provider, black_list):
        self.text2num_dict_provider = text2num_dict_provider or {}
        self.black_list = set(black_list or [])
        self._regex_ending = re.compile("-[а-яё]{1,3}(\s|$)")
        self._multiplier_numbers = [1e1, 1e2, 1e3, 1e6, 1e9, 1e12, 1e15, 1e18, 12]
        self._ordinal_number_endings = {"ий", "ый"}

    def __convert(self, numbers_info):
        # агрегируем собранную информацию в N чисел <= M токенов
        result_numbers = [[numbers_info[0][TOKEN_POS], numbers_info[0][ADJECTIVAL_POS]]]
        if not result_numbers[0][0].isdigit():  # токен может быть как "100", так и "сто". В кейсах типа "сто",
            # т.е. когда изначально числительное представлено словом, мы берем цифру
            result_numbers = [[numbers_info[0][NUMBER_POS], numbers_info[0][ADJECTIVAL_POS]]]
        prev_number_info = numbers_info[0]
        for number_info in numbers_info[1:]:
            if number_info[NOT_FROM_DICTIONARY_POS]:
                result_numbers.append([number_info[TOKEN_POS], number_info[ADJECTIVAL_POS]])
            else:
                if number_info[NUMBER_POS] in self._multiplier_numbers and \
                        number_info[NUMBER_POS] >= prev_number_info[NUMBER_POS]:
                    result_numbers[-1] = [get_number(str(result_numbers[-1][0])) * number_info[NUMBER_POS],
                                          number_info[ADJECTIVAL_POS]]
                    # надо обработать без пятнадцати шесть
                elif prev_number_info[BEZ_POS] and number_info[NUMBER_POS] in HOURS_RANGE and not \
                        number_info[TOKEN_POS].isdigit() and (number_info[TOKEN_POS].endswith("ь") or \
                                                              number_info[TOKEN_POS].lower() in BEG_LIST):
                    result_numbers = [[number_info[NUMBER_POS], number_info[ADJECTIVAL_POS]] for number_info in
                                      numbers_info]
                elif number_info[TOKEN_POS].isdigit() and \
                        len(str(number_info[NUMBER_POS])) > len(str(prev_number_info[NUMBER_POS])):
                    # защита от кейса 6 5
                    result_numbers[-1] = [get_number(str(result_numbers[-1][0])) + number_info[NUMBER_POS],
                                          number_info[ADJECTIVAL_POS]]
                elif not number_info[TOKEN_POS].isdigit() and \
                        len(str(number_info[NUMBER_POS])) < len(str(prev_number_info[NUMBER_POS])) and not \
                        prev_number_info[NUMBER_POS] in self.BLACK_LIST:
                    # но надо аккуратно с "тысяча восемьсот пятьдесят три"
                    result_numbers[-1] = [get_number(str(result_numbers[-1][0])) + number_info[NUMBER_POS],
                                          number_info[ADJECTIVAL_POS]]
                else:
                    result_numbers = [[number_info[NUMBER_POS], number_info[ADJECTIVAL_POS]] for number_info in
                                      numbers_info]
                    break
            prev_number_info = number_info
        return result_numbers

    def _check_if_sberbank_phone(self, token, previous_token):
        is_sberbank_phone = False
        if token in self.black_list:
            if NUMBER in previous_token or previous_token in ADPOSITIONS:
                is_sberbank_phone = True
        return is_sberbank_phone

    def __get_number(self, token_desc, i, previous_token, token_desc_list):
        info_tuple = None
        token = token_desc[TEXT].lower()
        token = " ".join(self._regex_ending.sub(" ", token).split())
        previous_word_is_bez = False
        if token not in self._ordinal_number_endings:
            num = get_number(token)
            is_sberbank_phone = self._check_if_sberbank_phone(token, previous_token)
            if num is not None and not is_sberbank_phone:
                if i > 0 and previous_token in BEZ_LIST:
                    previous_word_is_bez = True
                info_tuple = (token, num, True, token_desc, previous_word_is_bez, False)
            else:
                if token == KILO_PREFIX:
                    if i > 0 and len(token_desc_list) > 1 and token_desc_list[i - 1][TEXT].isdigit():
                        num = self.text2num_dict_provider.get(token)
                else:
                    num = self.text2num_dict_provider.get(token)
                if num is not None:
                    if i > 0 and previous_token in BEZ_LIST:
                        previous_word_is_bez = True
                    value = num[0]
                    is_adjective = num[1]
                    info_tuple = (token, value, False, token_desc, previous_word_is_bez, is_adjective)
        return info_tuple

    def __merge(self, tuple_buffer_list, numbers_list):
        without_changes = len(tuple_buffer_list) == len(numbers_list)
        out_list = []
        if without_changes:
            for token_tuple, num in zip(tuple_buffer_list, numbers_list):
                number = num[0]
                is_adjective = num[1]
                token_desc = token_tuple[META_TOKEN_POS]
                token_desc[TEXT] = str(number)  # beware '1e-07', кладем такое в текст
                token_desc[LEMMA] = str(number)  # beware '1e-07', кладем такое в лемму
                token_desc[TOKEN_TYPE] = NUM_TOKEN
                token_desc[TOKEN_VALUE] = {VALUE: get_number(str(number)), ADJECTIVAL_NUMBER: is_adjective}
                preliminary_dicti = {}
                preliminary_dicti[TOKEN_TYPE] = NUM_TOKEN
                preliminary_dicti[TOKEN_VALUE] = {VALUE: get_number(str(number)), ADJECTIVAL_NUMBER: is_adjective}
                if LIST_OF_TOKEN_TYPES_DATA not in token_desc:
                    token_desc[LIST_OF_TOKEN_TYPES_DATA] = []
                token_desc[LIST_OF_TOKEN_TYPES_DATA].append(preliminary_dicti)
                out_list.append(token_desc)
        else:
            for num in numbers_list:
                number = num[0]
                is_adjective = num[1]
                t = {TEXT: str(number), LEMMA: str(number), TOKEN_TYPE: NUM_TOKEN,
                     TOKEN_VALUE: {VALUE: get_number(str(number)), ADJECTIVAL_NUMBER: is_adjective}}
                t[LIST_OF_TOKEN_TYPES_DATA] = [{TOKEN_TYPE: NUM_TOKEN,
                                                TOKEN_VALUE: {VALUE: get_number(str(number)),
                                                              ADJECTIVAL_NUMBER: is_adjective}}]
                # beware '1e-07' in text and lemma
                out_list.append(t)
        return out_list

    def __call__(self, token_desc_list, *args):
        """
        Метод находит все записи чисел в виде цифр (120.5) и букв (сто двадцать),
        конвертирует их при необходимости в циферную запись и проставляет тип токена NUM_TOKEN.
        :param token_desc_list: (list of dicts)
        :return: out: Список из dicts (enriched)
        """
        buffer = []
        out = []
        previous_token = ""
        for i, token in enumerate(token_desc_list):
            number_info_tuple = self.__get_number(token, i, previous_token, token_desc_list)
            if number_info_tuple is not None:
                buffer.append(number_info_tuple)
            elif len(buffer) > 0:
                numbers = self.__convert(buffer)
                token_list = self.__merge(buffer, numbers)
                out.extend(token_list)
                buffer = []
                out.append(token)
            else:
                out.append(token)
            previous_token = token[TEXT]

        if len(buffer) > 0:
            numbers = self.__convert(buffer)
            token_list = self.__merge(buffer, numbers)
            out.extend(token_list)
        return out


class NumbersUnionAfterSTT:
    """
    Объединение цифр в строке
    """
    BLACK_LIST = set(range(10, 20))

    def __init__(self, text2num_dict_provider):
        self.text2num_dict_provider = text2num_dict_provider or {}
        self._regex_ending = re.compile("-[а-яё]{1,3}(\s|$)")
        self._multiplier_numbers = [1e3, 1e6, 1e9, 1e12, 1e15, 1e18]
        self._ordinal_number_endings = {"ий", "ый"}

    def __convert(self, numbers_info):
        # агрегируем собранную информацию в N чисел <= M токенов
        result_numbers = [numbers_info[0][TOKEN_POS]]
        if not result_numbers[0].isdigit():  # токен может быть как "100", так и "сто". В кейсах типа "сто",
            # т.е. когда изначально числительное представлено словом, мы берем цифру
            result_numbers = [numbers_info[0][NUMBER_POS]]
        prev_number_info = numbers_info[0]
        for number_info in numbers_info[1:]:
            if number_info[NUMBER_POS] in self._multiplier_numbers and \
                    number_info[NUMBER_POS] >= prev_number_info[NUMBER_POS]:
                result_numbers[-1] = get_number(str(result_numbers[-1])) * number_info[NUMBER_POS]
            elif len(str(number_info[NUMBER_POS])) < len(str(prev_number_info[NUMBER_POS])) and not \
                    prev_number_info[NUMBER_POS] in self.BLACK_LIST and number_info[NUMBER_POS] != 0:
                result_numbers[-1] = get_number(str(result_numbers[-1])) + number_info[NUMBER_POS]
            else:
                result_numbers.append(number_info[NUMBER_POS])
            prev_number_info = number_info
        return result_numbers

    def __get_number(self, token_desc, i, token_desc_list):
        info_tuple = None
        token = token_desc.lower()
        token = " ".join(self._regex_ending.sub(" ", token).split())
        num = None
        if token not in self._ordinal_number_endings:
            if token == KILO_PREFIX:
                if i > 0 and len(token_desc_list) > 1 and token_desc_list[i - 1].isdigit():
                    num = self.text2num_dict_provider.get(token)[0]
            else:
                num = self.text2num_dict_provider.get(token)
            if num is not None:
                info_tuple = (token, num[0], False, token_desc)
        return info_tuple

    def __call__(self, input_string, *args):
        """
        Метод находит все записи чисел в виде цифр (120.5) и букв (сто двадцать),
        конвертирует их при необходимости в циферную запись и проставляет тип токена NUM_TOKEN.
        :param input_string: исходная текстовая строка
        :return: строка, где цифры уже объединены
        """
        buffer = []
        out = []
        token_desc_list = input_string.split(" ")
        for i, token in enumerate(token_desc_list):
            number_info_tuple = self.__get_number(token, i, token_desc_list)
            if number_info_tuple is not None:
                buffer.append(number_info_tuple)
            elif len(buffer) > 0:
                numbers = self.__convert(buffer)
                zero_counter = False
                token_list = []
                for k, number in enumerate(numbers):
                    if zero_counter:
                        token_list.append(str(0) + str(number))
                        zero_counter = False
                    elif number == 0 and k < len(numbers) - 1:
                        zero_counter = True
                    else:
                        token_list.append(str(number))
                out.extend(token_list)
                buffer = []
                out.append(token)
            else:
                out.append(token)

        if len(buffer) > 0:
            numbers = self.__convert(buffer)
            zero_counter = False
            token_list = []
            for k, number in enumerate(numbers):
                if zero_counter:
                    token_list.append(str(0) + str(number))
                    zero_counter = False
                elif number == 0 and k < len(numbers) - 1:
                    zero_counter = True
                else:
                    token_list.append(str(number))
            out.extend(token_list)
        return " ".join(out)
