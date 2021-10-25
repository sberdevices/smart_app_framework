import re
import json
import time
import string
from typing import Dict

from core.text_preprocessing.constants import ANIMACY_TOKEN
from core.text_preprocessing.grammem.grammem_constants import TEXT, LEMMA, TOKEN_TYPE, LIST_OF_TOKEN_TYPES_DATA, \
    TOKEN_VALUE, VALUE, COMPOSITE_TOKEN_TYPE, IS_BEGINNING_OF_COMPOSITE, GRAMMEM_INFO, PART_OF_SPEECH, IS_STOP_WORD, \
    PART_OF_SPEECH_PYMORPHY

NUM_TOKEN = "NUM_TOKEN"
CUSTOM_PUNCTUATION = set(string.punctuation + "«»…=#-——–")
SENTENCE_ENDPOINT_TOKEN = "SENTENCE_ENDPOINT_TOKEN"


def flatten(lst: list) -> list:
    """
    Функция склеивает списки внутри списков, убирая один уровень вложенности
    Например, [ [1,2,3], [4,5,6], [[7,8],[9,10]] ] превращается в [1, 2, 3, 4, 5, 6, [7, 8], [9, 10]]
    """
    return [item for sublist in lst for item in sublist if item]


def reverse_json_dict(data):
    data = json.loads(data)
    result = dict()
    for key, values in data.items():
        for value in values:
            result[value] = key
    return result


def replace_by_dict(text: str, replace_rules: Dict[str, str]) -> str:
    for value, replacement in replace_rules.items():
        text = text.replace(value, replacement)
    return text


def revert_dict_with_list_values(dicti):
    new_dic = {}
    for k, v in dicti.items():
        for x in v:
            if x not in new_dic:
                new_dic[x] = k
    return new_dic


def replace_currencies_symbols(text: str) -> str:
    return replace_by_dict(text, {"$": " usd", "₽": " rur", "€": " eur"})


def extract_only_numeric(text: str) -> str:
    return ''.join([letter for letter in text if letter in "0123456789"])


def merge_numbers(text: str) -> str:
    """
    Класс предназначен для мержа номеров в одно число
    Например, "60 000 000" -> 60000000"

    :param text (string)
    :return: text(string)
    """
    tokens = text.split()
    result = tokens[0] if len(tokens) > 0 else ""
    for i in range(1, len(tokens)):
        if tokens[i].isdigit() and tokens[i - 1].isdigit():
            result += tokens[i]
        else:
            result = "{} {}".format(result, tokens[i])
    return result


def unmerge_numbers_and_letters(text: str) -> str:
    """
    Функция разбивает написанные вместе цифры и буквы. Например, "242р" -> "242 р"

    :param text (string)
    :return: result(string)
    """
    result = ''
    prev_letter = ''
    for letter in text:
        if (prev_letter.isalpha() and letter.isdigit()) or (prev_letter.isdigit() and letter.isalpha()):
            result = "{} {}".format(result, letter)
        else:
            result += letter
        prev_letter = letter
    return result


def lemma_modification(lemma: str) -> str:
    if len(lemma) > 1 and "." in lemma:
        res = lemma.strip(".")
        if "." in res:
            res = res.replace(".", "_")
    else:
        res = lemma
    return res


def return_lemmas_only(token_desc_list: list, include_sentence_endpoint: bool = True,
                       consider_stop_words: bool = False) -> str:
    """
    Конвертировать список токенов в строку без пунктуации, содержащую леммы и замены на тип токена.
    Предложения разделяются точкой. Если перед этим нет грамматической инфо - возвращается поле токена TEXT
    :param token_desc_list: Список токенов (дикты), include_sentence_endpoint -- принтить ли фейковую точку, bool
    :return: Строка, содержащую леммы и замены на тип токена.
    """
    final_line = []
    for token in token_desc_list:
        if COMPOSITE_TOKEN_TYPE in token:
            if token[IS_BEGINNING_OF_COMPOSITE]:
                token_type = token[COMPOSITE_TOKEN_TYPE]
            else:
                continue
        else:
            token_type = token.get(TOKEN_TYPE)
        if token_type != SENTENCE_ENDPOINT_TOKEN:
            grammem_info = token.get(GRAMMEM_INFO)
            if grammem_info is not None:
                pos = grammem_info.get(PART_OF_SPEECH_PYMORPHY)
                if pos != "PNCT":
                    if token_type is not None and token_type != ANIMACY_TOKEN:
                        final_line.append(token_type)
                    elif not token.get(IS_STOP_WORD) or (token.get(IS_STOP_WORD) and consider_stop_words):
                        lemma = lemma_modification(token.get(LEMMA))
                        final_line.append(lemma)
            else:
                final_line.append(token[TEXT])
        elif include_sentence_endpoint:
            final_line.append(token[TEXT])
    return " ".join(final_line)


class BaseNormalizePhoneNumbers(object):
    def __init__(self):
        self.boundary_start = '(?:[^\d\+]|^)'
        self.boundary_end = '(?:[^\d\-\:]|$)'
        self.plus_regex = re.compile(r"(\+ *)(\+7\d{10})")

    def remove_additional_phone_pluses(self, text: str) -> str:
        final_text = re.sub(self.plus_regex, r'\2', text)
        return final_text

    def _get_phone_numbers(self, text):
        return []

    def __call__(self, text: str) -> str:
        """
        На вход принимается строка
        На выходе имеем новую строку, где номера телефонов смержены в один токен

        :param text (string)
        :return: text(string)
        """
        already_done = []
        phone_numbers = self._get_phone_numbers(text)
        normalized_phone_numbers = []
        to_be_deleted = []
        for p in phone_numbers:
            digits = extract_only_numeric(p)[-10:]
            if digits[0] == "9":
                normalized_phone_numbers.append('+7' + digits)
            else:
                to_be_deleted.append(p)
        final_phone_numbers = [p for p in phone_numbers if p not in to_be_deleted]
        for normalized_pn, pn in zip(normalized_phone_numbers, final_phone_numbers):
            if (normalized_pn, pn.strip()) not in already_done:
                text = text.replace(pn.strip(), normalized_pn)
                already_done.append((normalized_pn, pn.strip()))
        text = self.remove_additional_phone_pluses(text)
        return text


class NormalizePhoneNumbers(BaseNormalizePhoneNumbers):
    def __init__(self):
        super(NormalizePhoneNumbers, self).__init__()
        self.phone_start = '(\+?[78]?'
        self.phone_delim = '[\s\-\(\)]?'
        self.phone_delim_with_dash = '[\) ][\- ]'
        self.phone_delim_dash_twice = '[\s\-\(\)]{,2}'

        t1 = "{}{}{}{}{}{}{}{}{}".format(self.phone_start, self.phone_delim, '\d{3}',
                                         self.phone_delim, '\d{3}', self.phone_delim, '\d{2}', self.phone_delim,
                                         '\d{2})')
        t2 = "{}{}{}{}{}{}{}{}{}".format(self.phone_start, self.phone_delim, '\d{4}',
                                         self.phone_delim, '\d{2}', self.phone_delim, '\d{2}', self.phone_delim,
                                         '\d{2})')
        t3 = "{}{}{}{}".format(self.phone_start, '\d{10}', self.phone_delim, ')')
        t4 = "{}{}{}{}{}{}{}{}{}".format(self.phone_start, self.phone_delim_dash_twice, '\d{3}',
                                         self.phone_delim_with_dash, '\d{3}', self.phone_delim, '\d{2}',
                                         self.phone_delim, '\d{2})')
        regex_phone_number_template = '|'.join([t1, t2, t3, t4])
        regex_phone_number_template = '{}(?:{}){}'.format(self.boundary_start, regex_phone_number_template,
                                                          self.boundary_end)

        self.regex_phone_number = re.compile(regex_phone_number_template)

    def _get_phone_numbers(self, text):
        return flatten(self.regex_phone_number.findall(text))


class NormalizePhoneNumbersVoice(BaseNormalizePhoneNumbers):
    def __init__(self):
        super(NormalizePhoneNumbersVoice, self).__init__()
        phone_start_1 = '\+?[78]'
        phone_start_2 = '9'
        phone_1 = '(([ \-]*\d){10})'
        phone_2 = '(([ \-]*\d){9})'

        t1 = "{}{}".format(phone_start_1, phone_1)

        t2 = "{}{}".format(phone_start_2, phone_2)

        regex_phone_number_template = '|'.join([t1, t2])

        regex_phone_number_template = '{}(?:{}){}'.format(self.boundary_start, regex_phone_number_template,
                                                          self.boundary_end)

        self.regex_phone_number = re.compile(regex_phone_number_template)

    def _get_phone_numbers(self, text):
        phone_numbers = []
        for z in self.regex_phone_number.finditer(text):
            phone_numbers.append(z.group(0))
        return phone_numbers


class MergeCardNumbers(object):
    def __init__(self):
        self._card_words = ["карта", "карты", "карте", "карту", "картой", "карт", "картах", "картам", "картами",
                            "виза", "visa", "мастеркард", "кард", "mastercard", "card", "maestro", "маэстро",
                            "мир"]
        self.words = "({}) ".format("|".join(self._card_words))
        self.card_regex = "((\d{4} \d{4} \d{4} \d{4})|(\d{4} \d{4} \d{10}))(?:(?!\d)|$)"
        self.regex_str = self.words + self.card_regex
        self._regex_card_number = re.compile(self.regex_str, re.IGNORECASE)

    def __call__(self, text: str) -> str:
        """
        Класс предназначен для мержа номеров карт в одно число при условии, что перед этим есть спец. слово
        Например, "карта 1234 1234 1234 1234" -> "карта 1234123412341234"

        :param text (string)
        :return: text(string)
        """
        for matched_tuple in self._regex_card_number.findall(text):
            card_word = matched_tuple[0]
            card_number = matched_tuple[1]
            text = text.replace("{} {}".format(card_word, card_number),
                                "{} {}".format(card_word, card_number.replace(' ', '')))
        return text


class MergeCardNumbersVoice(MergeCardNumbers):
    def __init__(self):
        super(MergeCardNumbersVoice, self).__init__()
        self.card_regex = '(([ ]*\d){16}(?:(?!\d)|$))'
        self.regex_str = self.words + self.card_regex
        self._regex_card_number = re.compile(self.regex_str, re.IGNORECASE)


class AdditionalMathSplitter(object):
    """
    Класс предназначен для дополнительного расспличивания по токенам для математического выражения.
    Деление уже ушло на этапе токенизации
    """

    def __init__(self):
        self.regexp = re.compile('(^|\s)(\d+([.,]\d+)?)(([*+\-^])(\d+([.,]\d+)?))+')
        self.str_of_delimiters = '*-^+'

    def __call__(self, text: str) -> str:
        searchen = re.search(self.regexp, text)
        if searchen:
            new_text = ''
            start_index = searchen.start()
            end_index = searchen.end()
            for i, char in enumerate(text):
                if start_index <= i <= end_index and char in self.str_of_delimiters:
                    new_text += " {} ".format(char)
                else:
                    new_text += char
        else:
            new_text = text
        return new_text


class UnicodeSymbolsConverter:
    """
    Замена юникодовых обозначений на человекочитаемые значки
    """

    def __init__(self, unicode_symbols: dict = None):
        self.unicode_dicti = unicode_symbols or dict()

    def __call__(self, text: str) -> str:
        '''
        :param text: str, текст, в котором будет произведена замена
        :return: текст, в котором юникодовая фигня заменена на человекочитаемые символы
        '''
        for key in self.unicode_dicti:
            text = text.replace(key, self.unicode_dicti[key])
        return text


class ReplaceSynonyms(object):
    """
    class to replace whole words in text avoiding replacements inside words based on regular expressions and synonyms dictionary from __init__
    example on "сбер": 'храните деньги в сберегательных кассах. сбер.' -> 'храните средства в сберегательных кассах. сбербанк.'
    requires lowered text without punctuation
    """

    def __init__(self, synonyms):
        self.synonyms = synonyms or {}

    def __call__(self, token_desc_list):
        """
        Класс предназначен для замены синонимов.
        На вход принимается список токенов
        На выходе имеем новый список токенов, где синонимы уже заменены

        :param token_desc_list (list of dicts)
        :return: token_desc_list (improved; list of dicts)
        """
        final_list_of_tokens = []
        skip = False
        for i, token in enumerate(token_desc_list):
            if skip:
                skip = False
            else:
                if len(token_desc_list) > i + 1 and \
                        "{} {}".format(token[TEXT].lower(), token_desc_list[i + 1][TEXT].lower()) in self.synonyms:
                    new_token = self.synonyms["{} {}".format(token[TEXT].lower(), token_desc_list[i + 1][TEXT].lower())]
                    if len(new_token.split(" ")) > 1:
                        to_extend = [{TEXT: token} for token in new_token.split(" ")]
                        final_list_of_tokens.extend(to_extend)
                    else:
                        final_list_of_tokens.append({TEXT: new_token})
                    skip = True
                elif token[TEXT].lower() in self.synonyms:
                    new_token = self.synonyms[token[TEXT].lower()]
                    if len(new_token.split(" ")) > 1:
                        to_extend = [{TEXT: token} for token in new_token.split(" ")]
                        final_list_of_tokens.extend(to_extend)
                    else:
                        final_list_of_tokens.append({TEXT: new_token})
                else:
                    final_list_of_tokens.append(token)
        return final_list_of_tokens


class CurrencyTokensOneIterationMerger(object):
    def __init__(self):
        self.currencies_list = ["rur", "коп", "копеек", "копейки", "копейка", "копейку", "копейками", "копейкой",
                                "копейкам",
                                "копейках", "копейке", "eur", "центом", "центу", "центе", "центах", "центами", "центы",
                                "usd", "aud", "cad", "цент", "цента", "центов", "sgd", "chf",
                                "jpy", "сена", "сены", "сен", "gbp", "пенни", "сантим", "сантима",
                                "сантимов", "dkk", "nok", "sek", "эре", "евроцент", "евроцента", "евроцентов",
                                "евроценту", "евроцентом", "евроценте", "евроцентах", "евроцентами", "евроценты",
                                "cny", "цзяо", "uah", "byn", "czk", "геллер", "геллера", "геллеров",
                                "egp", "пиастр", "пиастра", "пиастров", "try", "куруш", "куруша", "курушей",
                                "gel", "тетри", "amd", "лум", "сантим", "сантимах", "сантиму", "сантиме",
                                "сантимами", "сантима", "сантимов"]
        self.dicti_diminutives = {
            "usd": ["цент", "цента", "центов", "центом", "центу", "центе", "центах", "центами", "центы"],
            "eur": ["цент", "цента", "центов", "центом", "центу", "центе", "центах", "центами", "центы",
                    "евроцент", "евроцента", "евроцентов", "евроценту", "евроцентом", "евроценте", "евроцентах",
                    "евроцентами", "евроценты"],
            "rur": ["коп", "копеек", "копейки", "копейка", "копейку", "копейками", "копейках", "копейке", "копейкой",
                    "копейкам"],
            "sek": ["эре"],
            "dkk": ["эре"],
            "nok": ["эре"],
            "gbp": ["пенни"],
            "chf": ["сантим", "сантима", "сантимов", "сантимами", "сантимах", "сантиму", "сантиме", "сантимами"],
            "cad": ["цент", "цента", "центов", "центом", "центу", "центе", "центах", "центами", "центы"],
            "aud": ["цент", "цента", "центов", "центом", "центу", "центе", "центах", "центами", "центы"],
            "sgd": ["цент", "цента", "центов", "центом", "центу", "центе", "центах", "центами", "центы"],
            "jpy": ["сена", "сены"],
            "cny": ["цзяо"],
            "uah": ["коп", "копеек", "копейки", "копейка", "копейку", "копейками", "копейках", "копейке", "копейкой",
                    "копейкам"],
            "byn": ["коп", "копеек", "копейки", "копейка", "копейку", "копейками", "копейках", "копейке", "копейкой",
                    "копейкам"],
            "czk": ["геллер", "геллера", "геллеров"],
            "egp": ["пиастр", "пиастра", "пиастров"],
            "try": ["куруш", "куруша", "курушей"],
            "gel": ["тетри"],
            "amd": ["лум"]
        }
        self.final_small_currencies = flatten(list(self.dicti_diminutives.values()))
        self.denominator = 0.01
        self.backward_dict = revert_dict_with_list_values(self.dicti_diminutives)

    def _is_amount(self, tokenized_elements, i):
        return len(tokenized_elements) > i + 1 and tokenized_elements[i][TEXT].isdigit() and tokenized_elements[
            i + 1][TEXT].lower() in self.currencies_list

    def _denominator_are_ok(self, tokenized_elements, i):
        d1 = tokenized_elements[i + 1][TEXT].lower() if len(tokenized_elements) > i + 1 else None
        d2 = tokenized_elements[i - 1][TEXT].lower()
        if d2 in self.dicti_diminutives and d1 in self.dicti_diminutives[d2]:
            return True
        return False

    def _normalize_currency(self, tokenized_elements, i):
        if len(tokenized_elements) > i + 1 and tokenized_elements[i + 1][TEXT] in self.final_small_currencies:
            tokenized_elements[i][TEXT] = str(int(tokenized_elements[i][TEXT]) * self.denominator)
            tokenized_elements[i][TOKEN_VALUE][VALUE] *= self.denominator
            for dicti in tokenized_elements[i][LIST_OF_TOKEN_TYPES_DATA]:
                if dicti[TOKEN_TYPE] == NUM_TOKEN:
                    dicti[TOKEN_VALUE][VALUE] *= self.denominator
        return tokenized_elements[i]

    def _sum_2_amounts(self, final_tokenized_elements, tokenized_elements, i):
        final_tokenized_elements.append(self._normalize_currency(tokenized_elements, i))
        k = -1 if len(final_tokenized_elements) <= i else i
        final_tokenized_elements[k - 2][TEXT] = str(
            float(final_tokenized_elements[k - 2][TEXT]) + float(tokenized_elements[i][TEXT]))
        final_tokenized_elements[k - 2][TOKEN_VALUE][VALUE] += tokenized_elements[i][TOKEN_VALUE][VALUE]
        for dicti in final_tokenized_elements[k - 2][LIST_OF_TOKEN_TYPES_DATA]:
            if dicti[TOKEN_TYPE] == NUM_TOKEN:
                dicti[TOKEN_VALUE][VALUE] += tokenized_elements[i][TOKEN_VALUE][VALUE]
        final_tokenized_elements.pop(k)
        return final_tokenized_elements

    def __call__(self, tokenized_elements):
        """
        Класс предназначен для мержа валют -- переводить более мелкие (копейки и центы) в более крупные,
        а также мержить штуки вида 4 рубля 40 копеек в 4.4 рубля
        На вход принимается список токенов
        На выходе имеем список токенов, в котором смержены валюты

        :param tokenized_elements_list (list of dicts)
        :return: another tokenized_elements_list (list of dicts)
        """
        final_tokens = []
        skip, roubles = False, False
        for i in range(len(tokenized_elements)):
            if skip:
                skip = False
            elif roubles:
                other_currency = tokenized_elements[i][TEXT].lower()
                if other_currency in self.backward_dict:
                    final_tokens.append({TEXT: self.backward_dict[other_currency]})
                else:
                    final_tokens.append(tokenized_elements[i])
                roubles = False
            else:
                is_amount = self._is_amount(tokenized_elements, i)
                looks_like_2_amounts = is_amount and self._is_amount(tokenized_elements, i - 2) \
                                       and self._denominator_are_ok(tokenized_elements, i)
                if looks_like_2_amounts:
                    final_tokens = self._sum_2_amounts(final_tokens, tokenized_elements, i)
                    skip = True
                elif is_amount:
                    final_tokens.append(self._normalize_currency(tokenized_elements, i))
                    roubles = True
                else:
                    final_tokens.append(tokenized_elements[i])
        return final_tokens


class DateConverter:
    CENTURY = 100

    def __init__(self):
        self.regex = re.compile('(\d{1,2})[,\./\\\-](\d{1,2})[,\./\\\-](\d{4}|\d{2})')
        self.safe_regex_for_month_and_year = re.compile('(\d{1,2})[\\\/](\d{4}|\d{2})')

    def _year_preprocessing(self, year):
        tm_year_now = time.localtime().tm_year
        self.CENTURY_start = (tm_year_now // self.CENTURY) * self.CENTURY
        if year < self.CENTURY:
            if year <= 90:  # tm_year_now - self.CENTURY_start
                year += self.CENTURY_start
            else:
                year += self.CENTURY_start - self.CENTURY
        return year

    def __call__(self, word):
        r = self.regex.findall(word)
        safe_dates = self.safe_regex_for_month_and_year.findall(word)
        try:
            r = [int(i) for i in r[0]]
            r[2] = self._year_preprocessing(r[2])
            if r[1] > 12:
                r = [r[1], r[0], r[2]]
            result = {'day': r[0], 'month': r[1], 'year': r[2]}
        except (IndexError, ValueError):
            if safe_dates:
                r = [int(i) for i in safe_dates[0]]
                r[1] = self._year_preprocessing(r[1])
                result = {'month': r[0], 'year': r[1]}
            else:
                result = None

        return result


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
