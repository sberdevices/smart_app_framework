"""
Модуль для определения временного периода из текста на русском языке
!!! Модуль работает только со словами в нижнем регистре !!!

usage: begin_date, end_date = period_determiner(words_to_process)
"""

import re
from typing import List, Tuple, Optional
from datetime import datetime, timedelta


# глобальный формат даты
date_format: str = '%d.%m.%Y'
# шаблоны регулярок для определения дат
re_shortest_date_pattern = '^([0-9]{1,2})\\.([0-9]{1,2})$'
re_short_date_pattern = '^([0-9]{1,2})\\.([0-9]{1,2})\\.([0-9]{2})$'
re_long_date_pattern = '^([0-9]{1,2})\\.([0-9]{1,2})\\.([0-9]{4})$'


class IncorrectDateException(Exception):
    pass


class StateMachineForDateDetermining:
    """
    Класс конечный-автомат (КА) для определения даты из строки на русском языке.
    Работает следующим образом:
    на вход в КА передаем последовательно слова, каждое новое слово влияет на состояние КА
    и КА понимает какой период времени пытаемся сообщить,
    а также КА может понять, что дата определена некорректно
    """

    # начальное пустое состояние автомата до прихода первого слова
    _empty_state: bool

    # Истина, если используется период до текущего дня
    # иначе конкретная дата (день, месяц, квартал, год)
    _is_period: bool
    _is_determined: bool
    _is_error: bool
    _date_period: List[Optional[datetime]]
    _day: int
    _month: int
    _year: int

    # список следующих ожидаемых слов
    # если это слово не получено, то ошибка
    # например: если пришло "вчерашний", то ждем слово "день"
    # если любое следующее слово ошибка, как в случае текста "сегодня",
    # то _next_expected_words = []
    # если не рассматриваем следующие слова, то _next_expected_words = None
    _next_expected_words: Optional[List[str]]

    # дескриптор относительного периода:
    #  1 - указание на текущий период - нынешний, текущий, сегодняшний, этот
    #  0 - отсутствует
    # -1 - указание на прошлый период - вчерашний, вчера, прошлый, предыдущий
    _relative_descriptor: int

    # при поступлении числа в КА мы еще не понимаем к чему относится число,
    # поэтому сохраняем его в self._quantifier, но как только мы его использовали,
    # то сразу его обнуляем для приему следующего числа
    _quantifier: int

    def __init__(self):
        self._empty_state = True
        self._is_period = False
        self._current_date = datetime.now()
        self._date_period = [None, None]
        self._relative_descriptor = 0
        self._quantifier = 0
        self._day = 0
        self._month = 0
        self._year = 0
        self._is_determined = False
        self._is_error = False
        self._next_expected_words = None

    def has_errors(self):
        return self._is_error

    @property
    def result(self) -> Tuple[Optional[str], Optional[str]]:
        if self._is_error:
            return 'error', 'error'

        if self._is_determined:
            # если дата считается определенной, но остался неиспользуемый квантификатор,
            # то это ошибка
            if self._quantifier:
                return 'error', 'error'

            # если указали 1ую дату в периоде
            if self._date_period[0]:
                # если год определен, то надо его использовать
                if self._year:
                    try:
                        self._date_period[0] = safe_datetime(
                            year=self._year,
                            month=self._date_period[0].month,
                            day=self._date_period[0].day
                        )
                    except IncorrectDateException:
                        return 'error', 'error'

                # если работаем с периодом или дата относительна текущей даты,
                # то конец периода всегда окончивается текущей датой
                # пример: "с 12 мая" или "за 4 прошлых месяца"
                if self._is_period or self._relative_descriptor:
                    # берем текущий день в качестве окончания
                    self._date_period[1] = self._current_date
                else:
                    # иначе берем расчитанную 2ую дату
                    if self._date_period[1]:
                        # если год определен, то надо его использовать
                        if self._year:
                            try:
                                self._date_period[1] = safe_datetime(
                                    year=self._year,
                                    month=self._date_period[1].month,
                                    day=self._date_period[1].day
                                )
                            except IncorrectDateException:
                                return 'error', 'error'
                    else:
                        # если она пустая, то берем текущую дату
                        self._date_period[1] = self._current_date

                return format_date(self._date_period[0]), format_date(self._date_period[1])

            else:
                # Иначе строим дату начала на основе года, месяца и дня,

                # для частного случая когда указан только год
                if self._day == 0 and self._month == 0 and self._year:
                    self._date_period[0] = safe_datetime(self._year, 1, 1)

                    # если имеем дело с периодом когда в начале фразы союз "с" или "со"
                    if self._is_period:
                        # берем текущий день в качестве окончания
                        self._date_period[1] = self._current_date
                    else:
                        # иначе конец указанного года
                        self._date_period[1] = safe_datetime(self._year, 12, 31)

                    return format_date(self._date_period[0]), format_date(self._date_period[1])

                # если день не указан, тогда берем первый день
                if self._day == 0:
                    self._day = 1
                # если месяц не указан, тогда берем первый месяц
                if self._month == 0:
                    self._month = 1
                # если год не указан, тогда берем текущий год
                if self._year == 0:
                    self._year = self._current_date.year

                try:
                    self._date_period[0] = safe_datetime(self._year, self._month, self._day)
                except IncorrectDateException:
                    return 'error', 'error'

                # берем текущий день в качестве окончания
                self._date_period[1] = self._current_date

                return format_date(self._date_period[0]), format_date(self._date_period[1])

        return '', ''

    def input(self, word: str):
        """
        Ключевой метод КА принимающий слова и меняющий свое состояние в зависимости от этого
        """

        try:

            # если предлоги "от" или "с" идут не первыми словами, то это ошибка
            if word == 'с' or word == 'со' or word == 'от':
                if self._empty_state:
                    # зафиксировали что имеем дело с периодом
                    self._is_period = True
                    return
                else:
                    self._is_error = True
                    return

            # после прихода первого слова начальное состояние теряется
            if self._empty_state:
                self._empty_state = False

            # если в КА ошибка, то он больше не обрабатывает слова
            if self._is_error:
                return

            # если ждем какое-то слово
            if self._next_expected_words:
                if word not in self._next_expected_words:
                    self._is_error = True
                    return
                self._next_expected_words = None
            # если _next_expected_words пустой список,
            # то больше не ждем никаких слов
            # и любое пришедшее слово приводит к ошибке
            elif self._next_expected_words == []:
                self._is_error = True
                return

            # проверка через регулярку дат формата dd.mm.yy
            m = re.match(re_short_date_pattern, word)
            if m:
                self._date_period[0] = self._date_period[1] = \
                    safe_datetime(
                        year=2000 + int(m.group(3)),
                        month=int(m.group(2)),
                        day=int(m.group(1))
                    )
                self._is_determined = True
                return

            # проверка через регулярку дат формата dd.mm.yyyy
            m = re.match(re_long_date_pattern, word)
            if m:
                self._date_period[0] = self._date_period[1] = \
                    safe_datetime(
                        year=int(m.group(3)),
                        month=int(m.group(2)),
                        day=int(m.group(1))
                    )
                self._is_determined = True
                return

            # проверка через регулярку дат формата dd.mm
            m = re.match(re_shortest_date_pattern, word)
            if m:
                self._date_period[0] = self._date_period[1] = \
                    safe_datetime(
                        year=self._current_date.year,
                        month=int(m.group(2)),
                        day=int(m.group(1))
                    )
                self._is_determined = True
                return

            # передаем число в КА
            if word.isnumeric():
                # квантификатор уже определен
                if self._quantifier:
                    self._is_error = True
                    return
                # иначе
                else:
                    self._quantifier = int(word)
                    if self._quantifier > 1900:
                        self._year = self._quantifier
                        self._quantifier = 0

            # иначе если в КА прилетело слово
            else:
                # год
                if match_word_with_list(word, ['год', 'лет']) != -1:
                    if self._quantifier:
                        # год должен быть 4х-значным и больще 1900 года
                        if self._quantifier > 1900:
                            self._year = self._quantifier
                            self._quantifier = 0
                    # указан относительный период
                    if self._relative_descriptor:
                        if self._relative_descriptor > 0:
                            self._year = self._current_date.year
                        else:
                            # квантификатор нужен для примера: 2 прошлых года
                            self._year = self._current_date.year - 1 * (self._quantifier if self._quantifier else 1)
                            self._quantifier = 0
                    else:
                        # если относительный период не указан,
                        # то период определяем как (365 * self._quanifier) дней ранее
                        # пример: за год - значит с периода 365 дней ранее по сегодня
                        if self._month == 0 and self._year == 0:
                            self._date_period[0] = \
                                self._current_date \
                                - timedelta(
                                    days=365 * (self._quantifier if self._quantifier else 1)
                                )
                            self._quantifier = 0

                    self._is_determined = True
                # месяц
                elif match_word_with_list(word, ['месяц']) != -1:
                    # указан относительный период
                    if self._relative_descriptor > 0:
                        self._month = self._current_date.month
                    elif self._relative_descriptor < 0:
                        # квантификатор нужен для примера: 2 прошлых месяца
                        delta_month = self._quantifier if self._quantifier else 0
                        if self._current_date.month < delta_month:
                            self._month = 12 + self._current_date.month - delta_month
                            self._year = self._current_date.year - 1
                        else:
                            self._month = self._current_date.month - delta_month
                            self._year = self._current_date.year
                        self._quantifier = 0
                    else:
                        # если относительный период не указан,
                        # то период определяем как (30 * self._quanifier) дней ранее
                        # пример: за месяц - значит с периода 30 дней ранее по сегодня
                        self._date_period[0] = \
                            self._current_date \
                            - timedelta(
                                days=30 * (self._quantifier if self._quantifier else 1)
                            )
                        self._quantifier = 0

                    self._is_determined = True
                # день
                elif match_word_with_list(word, ['ден', 'дня', 'дней']) != -1:
                    # указан относительный период
                    if self._relative_descriptor > 0:
                        self._date_period[0] = self._current_date
                    else:
                        # квантификатор нужен для примера: 2 прошлых дня
                        # когда квантификатор = 0, как в примере - за день,
                        # то это значит со вчерашнего дня
                        self._date_period[0] = self._current_date \
                            - timedelta(
                                days=self._quantifier if self._quantifier else 1
                            )

                        self._quantifier = 0

                    self._is_determined = True
                # неделя
                elif match_word_with_list(word, ['недел']) != -1:
                    # всегда относительный текущего дня период
                    self._date_period[0] = self._current_date \
                        - timedelta(
                            days=7 * (self._quantifier if self._quantifier else 1)
                        )

                    self._quantifier = 0

                    self._is_determined = True
                # квартал
                elif match_word_with_list(word, ['квартал']) != -1:
                    if self._quantifier:
                        if not (self._quantifier in [1, 2, 3, 4]):
                            self._is_error = True
                    else:
                        if self._current_date.month in [1, 2, 3]:
                            self._quantifier = 1
                        elif self._current_date.month in [4, 5, 6]:
                            self._quantifier = 2
                        elif self._current_date.month in [7, 8, 9]:
                            self._quantifier = 3
                        else:
                            self._quantifier = 4

                    self._date_period[0] = \
                        safe_datetime(
                            year=self._current_date.year,
                            month=3 * self._quantifier - 2,
                            day=1
                        )

                    if self._quantifier == 4:
                        self._date_period[1] = \
                            safe_datetime(
                                year=self._current_date.year + 1,
                                month=1,
                                day=1
                            ) - timedelta(days=1)
                    else:
                        self._date_period[1] = \
                            safe_datetime(
                                year=self._current_date.year,
                                month=3 * self._quantifier + 1,
                                day=1
                            ) - timedelta(days=1)

                    self._quantifier = 0
                    self._is_determined = True

                # другие слова
                else:
                    if match_word_with_list(word, ['вчерашн']) != -1:
                        self._next_expected_words = ['день']
                        self._relative_descriptor = -1
                    elif match_word_with_list(word, ['вчера']) != -1:
                        self._date_period[0] = self._date_period[1] = \
                            self._current_date - timedelta(days=1)
                        self._next_expected_words = []
                        self._is_determined = True
                    elif match_word_with_list(word, ['сегодн', 'ныне']) != -1:
                        self._date_period[0] = self._date_period[1] = \
                            self._current_date
                        self._next_expected_words = []
                        self._is_determined = True
                    elif match_word_with_list(word, ['сегодняшн']) != -1:
                        self._next_expected_words = ['день']
                        self._relative_descriptor = 1

                    else:
                        # обрабатваем месяца
                        months = [
                            'январ',
                            'феврал',
                            'март',
                            'апрел',
                            'ма',
                            'июн',
                            'июл',
                            'август',
                            'сентябр',
                            'октябр',
                            'ноябр',
                            'декабр'
                        ]
                        month_index = match_word_with_list(word, months)
                        if month_index != -1:
                            self._month = month_index + 1
                            if self._quantifier:
                                self._day = self._quantifier
                                self._quantifier = 0

                            if self._day:
                                self._date_period[0] = self._date_period[1] = safe_datetime(
                                    year=self._current_date.year,
                                    month=self._month,
                                    day=self._day
                                )
                            else:
                                self._date_period[0] = safe_datetime(
                                    year=self._current_date.year,
                                    month=self._month,
                                    day=1
                                )

                                self._date_period[1] = \
                                    safe_datetime(
                                        year=self._current_date.year + 1 if self._month == 12 else self._current_date.year,
                                        month=1 if self._month == 12 else self._month + 1,
                                        day=1
                                    ) - timedelta(days=1)

                            self._is_determined = True
                            return

                        pos_relative_descriptors = [
                            'текущ',
                            'нынешн',
                            'этот',
                            'эт'
                        ]
                        if match_word_with_list(word, pos_relative_descriptors) != -1:
                            self._relative_descriptor = 1
                            return

                        neg_relative_descriptors = [
                            'прошл',
                            'предыдущ'
                        ]
                        if match_word_with_list(word, neg_relative_descriptors) != -1:
                            self._relative_descriptor = -1
                            return

        except IncorrectDateException:
            self._is_error = True


def format_date(date: Optional[datetime]) -> str:
    if date:
        return date.strftime(date_format)
    return 'error'


def safe_datetime(year: int, month: int, day: int) -> Optional[datetime]:
    # исправление ошибки для февраля високосного года:
    # в невисокрсный год (не кратный 4) не может быть дня 29 февраля
    if year % 4 != 0 and month == 2 and day == 29:
        return datetime(year=year, month=month, day=28)
    # для всех остальных случаев в случае
    # при передачи некорректой комбинации года, месяца и дня
    # будем возвращать None
    else:
        try:
            return datetime(year=year, month=month, day=day)
        except ValueError as exc:
            raise IncorrectDateException('Некорректная дата') from exc


def match_word_with_list(word_to_check: str, list_of_pattern_words: List[str]) -> int:
    """
    Проверяем слово на вхождение в список слов, указанных без окончания.
    Примеры:
    match_word_with_list("года", ["год"]) == True
    match_word_with_list("май", ["ма", "июн", "июл"]) == True
    match_word_with_list("мая", ["ма", "июн", "июл"]) == True
    match_word_with_list("зима", ["весн", "лет", "осен", "зим"]) == True

    :param word_to_check: проверяемое слово
    :param list_of_pattern_words: список слово без окончания
    :return: индекс слова совпадающего в списке, -1 - если совпадения нет
    """
    i: int = 0
    for pattern_word in list_of_pattern_words:
        # окончание это комбинация букв длинной до 3 символов
        # сначала думал что гласные только должны быть,
        # но окончание "ых" в слове "прошлых" заставило использова все буквы
        pattern_str: str = '^' + pattern_word + '[а-я]{0,3}$'
        if re.match(pattern_str, word_to_check):
            return i
        i += 1

    return -1


def is_from_date_dictionary(word: str) -> bool:
    """
    Функция определяет входит ли слово
    в "словарь" описывающий период времени
    """

    # некоторые слова лишены окончания для нивелирования влияния падежей
    list_of_dictionary: List[str] = [
        "от",
        "с",
        "со",
        "по",
        "до",
        "вчерашн",
        "вчера",
        "прошл",
        "текущ",
        "этот",
        "эт",
        "ныне",
        "нынешн",
        "сегодн",
        "сегодняшн",
        "день",
        "дня",
        "месяц",
        "год",
        "лет",
        "недел",
        "квартал",
        "январ",
        "феврал",
        "март",
        "апрел",
        "ма",
        "июн",
        "июл",
        "август",
        "сентябр",
        "октябр",
        "ноябр",
        "декабр"
    ]
    if match_word_with_list(word, list_of_dictionary) == -1:
        return False
    return True


def period_determiner(words_to_process: List[str],
                      max_days_in_period: Optional[int] = None,
                      future_days_allowed: bool = False) -> Tuple[str, str]:
    """
    Входная функция модуля, ее вызываем для получения дат.
    Она использует рабочую функцию date_determiner

    :param words_to_process: список слово в нижнем регистре
    :param max_days_in_period: максимальное количество дней в периоде
    :param future_days_allowed: нужно ли ограничивать период сегодняшним днем
    :return: кортеж строк дат в формате dd.mm.yyyy,
    если одна из них или обе ошибочные, то error
    """

    # проверяем не указаны ли начало и конец периода
    # с помощью слов "по" или "до"
    i = 0
    try:
        i = words_to_process.index('по')
    except ValueError as exc:
        pass

    if not i:
        try:
            i = words_to_process.index('до')
        except ValueError as exc:
            pass

    begin_of_period: str = ''
    end_of_period: str = ''

    # указаны начало и конец периода с помощью слов "по" или "до",
    if i:
        begin_of_period, _ = date_determiner(words_to_process[:i])
        _, end_of_period = date_determiner(words_to_process[i+1:])

        # в русском языке период можно выбрать еще вот как:
        # с 2 по 13 апреля 2021 - первый период номером дня,
        # а вторая дата в обучной форме.
        # Обрабатываем этот случай после КА
        if (begin_of_period == 'error' or begin_of_period == '') and \
                end_of_period != '' and end_of_period != 'error':
            j: int = len(words_to_process[:i])
            if j <= 2:
                if words_to_process[j-1].isnumeric():
                    d1 = int(words_to_process[j-1])
                    m = re.match(re_long_date_pattern, end_of_period)
                    if m:
                        d2 = int(m.group(1))
                        m2 = m.group(2)
                        y2 = m.group(3)
                        if d1 > d2:
                            return 'error', 'error'
                        else:
                            begin_of_period = '{}.{}.{}'\
                                .format(d1 if d1 > 9 else '0' + str(d1), m2, y2)


    # иначе имеем дело со словами, указывающих на единственную дату
    else:
        begin_of_period, end_of_period = date_determiner(words_to_process)

    # дата начала не должна быть больше даты окончания периода
    if re.match(re_long_date_pattern, begin_of_period) \
            and re.match(re_long_date_pattern, end_of_period):
        begin_date: datetime = datetime.strptime(begin_of_period, date_format)
        end_date: datetime = datetime.strptime(end_of_period, date_format)
        if begin_date > end_date:
            return 'error', 'error'
        else:
            # контроль максимального количества дней в выбранном периоде
            if max_days_in_period:
                t: timedelta = end_date - begin_date
                if t.days > max_days_in_period:
                    return 'error', 'error'
            # контроль будущих дат
            if not future_days_allowed:
                current_day: datetime = datetime.now()
                if begin_date > current_day:
                    return 'error', 'error'
                if end_date > current_day:
                    end_of_period = format_date(current_day)

    return begin_of_period, end_of_period


def date_determiner(words_to_process: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Функция определяет дату на основе переданных слов на русском языке
    Краеугольная функция всего модуля.

    :param words_to_process:
    :return: картеж дат в формате dd.mm.yyyy или error, error в случае ошибки
    """

    state_machine = StateMachineForDateDetermining()
    for word in words_to_process:
        state_machine.input(word)
        if state_machine.has_errors():
            return 'error', 'error'

    return state_machine.result


def extract_words_describing_period(words_from_intent: List[str]) -> List[str]:
    """
    Функция извлекает список слов, описываюищих период,
    для последующей передачи функциям для определения периода

    :param words_from_intent: все слова из предложения в нижнем регистре
    :return: список слов описывающих период
    """

    words_to_process: List[str] = []
    for word in words_from_intent:
        if word.isnumeric() \
            or is_from_date_dictionary(word) \
                or re.match(re_shortest_date_pattern, word) \
                or re.match(re_short_date_pattern, word) \
                or re.match(re_long_date_pattern, word):
            words_to_process.append(word)

    return words_to_process

