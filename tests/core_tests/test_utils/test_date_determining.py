"""
Модуль для модульного тестирования работы period_determiner

Автор: Нурманов Алишер
Дата: октябрь 2021 года
"""

from datetime import datetime, timedelta
from core.utils.period_determiner import period_determiner
from core.utils.period_determiner import extract_words_describing_period


__author__ = 'out-nurmanov-as'


def test_period_determiner():
    current_date: datetime = datetime.now()

    # если используется форма "с месяца года по ныне"
    words_to_process = [
        'марта',
        '2019',
        'года',
        'по',
        'ныне'
    ]
    result = period_determiner(words_to_process)
    assert result == ('01.03.2019', '{}.{}.{}'.format(current_date.day, current_date.month, current_date.year))

    # если используется форма "за месяц год по сегодняшний день"
    words_to_process = [
        'марта',
        '2019',
        'года',
        'по',
        'сегодняшний',
        'день',
    ]
    result = period_determiner(words_to_process)
    assert result == ('01.03.2019', '{}.{}.{}'.format(current_date.day, current_date.month, current_date.year))

    # если используется полная форма
    words_to_process = [
        'марта',
        '2019',
        'года',
        'по',
        '15',
        'июня',
        '2021',
    ]
    result = period_determiner(words_to_process)
    assert result == ('01.03.2019', '15.06.2021')

    # если дата начала больше даты окончания периода
    words_to_process = [
        'марта',
        '2019',
        'года',
        'по',
        '15',
        'июня',
        '2010',
    ]
    result = period_determiner(words_to_process)
    assert result == ('error', 'error')

    # если используется форма "за несколько прошлых месяцев"
    delta_month = 4
    words_to_process = [
        str(delta_month),
        'прошлых',
        'месяца'
    ]
    result = period_determiner(words_to_process)

    month: int = 0
    year: int = 0
    if delta_month > current_date.month:
        month = 12 + current_date.month - delta_month
        year = current_date.year - 1
    else:
        month = current_date.month - delta_month
        year = current_date.year

    assert result == (
        '01.{}.{}'.format(month if month > 9 else '0' + str(month), year),
        '{}.{}.{}'.format(current_date.day, current_date.month, current_date.year)
    )

    # если используется форма "за несколько прошлых дня"
    delta_day = 4
    words_to_process = [
        str(delta_day),
        'прошлых',
        'дня'
    ]
    result = period_determiner(words_to_process)
    d = current_date - timedelta(days=delta_day)

    day = d.day if d.day > 9 else '0' + str(d.day)
    month = d.month if d.month > 9 else '0' + str(d.month)
    year = d.year

    assert result == (
        '{}.{}.{}'.format(day, month, year),
        '{}.{}.{}'.format(current_date.day, current_date.month, current_date.year)
    )

    # если переданы год и месяц
    words_to_process = [
        '2013',
        'июнь'
    ]
    result = period_determiner(words_to_process)
    assert result == ('01.06.2013', '30.06.2013')

    # если корректные даты переданы в формате dd.mm.yy и dd.mm.yyyy
    words_to_process = [
        '28.01.12',
        'до',
        '12.03.2020',
    ]
    result = period_determiner(words_to_process)
    assert result == ('28.01.2012', '12.03.2020')

    # если даты передана в формате dd.mm
    words_to_process = [
        '28.01'
    ]
    result = period_determiner(words_to_process)
    assert result == ('28.01.{}'.format(current_date.year), '28.01.{}'.format(current_date.year))

    # если конкретный квартал ипользуется
    words_to_process = [
        '3',
        'квартал',
        '2020',
    ]
    result = period_determiner(words_to_process)
    assert result == ('01.07.2020', '30.09.2020')

    # если начиная с определенного квартала
    words_to_process = [
        'с',
        '3',
        'квартала',
        '2020',
    ]
    result = period_determiner(words_to_process)
    assert result == ('01.07.2020', '{}.{}.{}'.format(current_date.day, current_date.month, current_date.year))

    # если одна из дат некорректная
    words_to_process = [
        '34.01.2003',
        'до',
        '12.03.2020',
    ]
    result = period_determiner(words_to_process)
    assert result == ('error', '12.03.2020')

    # если передать две даты с союзом "и" между ними, то определится только последняя
    words_to_process = [
        '31.01.2003',
        'и',
        '12.03.2020',
    ]
    result = period_determiner(words_to_process)
    assert result == ('12.03.2020', '12.03.2020')

    # если на обработку попадут слова не связанные с периодами времени
    words_to_process = [
        'ytgjy',
        'до',
        'sdfdasq0',
    ]
    result = period_determiner(words_to_process)
    assert result == ('error', 'error')

    # если используется только месяц
    words_to_process = [
        'март'
    ]
    result = period_determiner(words_to_process)
    assert result == ('01.03.{}'.format(current_date.year), '31.03.{}'.format(current_date.year))

    # если используется некорретная форма к примеру за март 28 2020 года
    words_to_process = [
        'март',
        '28',
        '2020',
        'года'
    ]
    result = period_determiner(words_to_process)
    assert result == ('error', 'error')

    # если используется некорректная форма к примеру "за март 28",
    words_to_process = [
        'март',
        '28'
    ]
    result = period_determiner(words_to_process)
    assert result == ('error', 'error')

    # если используется корректная форма к примеру "за 28 марта",
    # то определится как 28 марта текущего года
    words_to_process = [
        '28',
        'марта',
    ]
    result = period_determiner(words_to_process)
    assert result == ('28.03.{}'.format(current_date.year), '28.03.{}'.format(current_date.year))

    # если используется корректная форма к примеру "за 28 марта",
    # то определится как 28 марта текущего года
    words_to_process = [
        '28',
        'марта',
        '2019'
    ]
    result = period_determiner(words_to_process)
    assert result == ('28.03.2019', '28.03.2019')


    # если используется корректная форма к примеру "с 28 марта 2019",
    # то период определится как  с 28 марта 2019 года по сегодня
    words_to_process = [
        'с',
        '28',
        'марта',
        '2019',
    ]
    result = period_determiner(words_to_process)
    assert result == ('28.03.2019', '{}.{}.{}'.format(current_date.day, current_date.month, current_date.year))


def test_extract_words_describing_period():
    words_from_intent = [
        "заказать",
        "выписку",
        "за",
        "3",
        "квартал",
        "2020",
        "года"
    ]
    result = extract_words_describing_period(words_from_intent)
    assert result == ['3', 'квартал', '2020', 'года']

    words_from_intent = [
        "заказать",
        "выписку",
        "с",
        "марта",
        "2019",
        "года",
        "по",
        "ныне"
    ]
    result = extract_words_describing_period(words_from_intent)
    assert result == ['с', 'марта', '2019', 'года', 'по', 'ныне']

    words_from_intent = [
        "заказать",
        "за",
        "4",
        "прошлых",
        "месяца",
        "выписку"
    ]
    result = extract_words_describing_period(words_from_intent)
    assert result == ['4', 'прошлых', 'месяца']
