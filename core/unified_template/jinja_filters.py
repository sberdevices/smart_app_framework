import base64
import codecs
import json
import functools
import jinja2
import datetime
import pymorphy2
import uuid
import ics
import hashlib
import random
from pymorphy2.shapes import restore_capitalization
from core.unified_template.num2ordinal import Num2Ordinal
from core.unified_template.num2text import Num2Text
from urllib.parse import quote, unquote
from core.unified_template.currency2text import Money2Text, CURRENCY_CODE_2_NAME_MAP
from core.unified_template.pan2service import pan2service

morph = pymorphy2.MorphAnalyzer()
num2text = Num2Text()
num2ord = Num2Ordinal(num2text=num2text)
money2text = Money2Text(morph=morph)


def inflect(morph, text, required_grammemes):
    inflected = []
    for token in text.split():
        inflected_Parse_obj = morph.parse(token)[0].inflect(set(required_grammemes))
        inflected.append(restore_capitalization(inflected_Parse_obj.word, token) if inflected_Parse_obj else token)
    return " ".join(inflected)


def add_timedelta(date_time, *args, **kwargs):
    return date_time + datetime.timedelta(*args, **kwargs)


def okko_sec2text(s):
    h = int(s / 3600)
    m = int((s - h * 3600) / 60)
    return "{} ч {} мин".format(h, m) if h else "{} мин".format(m)


def generate_ics(date):
    calendar = ics.Calendar()
    event = ics.Event(begin=date)
    calendar.events.add(event)
    return str(calendar)


def timestamp_to_datetime(timestamp, utc_offset=0):
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc) + datetime.timedelta(seconds=utc_offset)


def wrap_datetime(day, month, year, hour, minute, utc_offset=0):
    datetime_ = datetime.datetime(
        day=day, month=month, year=year, hour=hour, minute=minute, tzinfo=datetime.timezone.utc
    )
    return datetime_ + datetime.timedelta(seconds=utc_offset)


@jinja2.environmentfilter
def co_sort(
        environment, value, reverse=False, attribute=None, order=None,
):
    # custom order sort

    order = order or []

    def index(item):
        try:
            return order.index(item)
        except ValueError:
            return int(functools.reduce(lambda x, y: str(x) + str(y), map(ord, item)))

    key_func = jinja2.filters.make_attrgetter(
        environment, attribute,
        postprocess=index
    )
    return sorted(value, key=key_func, reverse=reverse)


def phone_number_ru(number):
    """Convert a 10 character string into +7(xxx) xxx-xx-xx."""
    first = number[0:3]
    second = number[3:6]
    third = number[6:8]
    fourth = number[8:10]
    return f"+7 ({first}) {second}-{third}-{fourth}"


def timestamp_to_date(raw_datetime):
    ru_month_names = {1: 'января',
                      2: 'февраля',
                      3: 'марта',
                      4: 'апреля',
                      5: 'мая',
                      6: 'июня',
                      7: 'июля',
                      8: 'августа',
                      9: 'сентября',
                      10: 'октября',
                      11: 'ноября',
                      12: 'декабря'}

    client_datetime = int(str(raw_datetime)[:10])

    stamp_datetime = datetime.datetime.fromtimestamp(client_datetime)
    normal_day, month_number = stamp_datetime.day, stamp_datetime.month
    show_date = f'{normal_day} {ru_month_names[month_number]}'

    return show_date

# functions
jinja2.defaults.DEFAULT_NAMESPACE["datetime_today"] = datetime.datetime.today
jinja2.defaults.DEFAULT_NAMESPACE["now"] = datetime.datetime.utcnow
jinja2.defaults.DEFAULT_NAMESPACE["uuid4"] = lambda: str(uuid.uuid4())
jinja2.defaults.DEFAULT_NAMESPACE["timestamp_to_datetime"] = timestamp_to_datetime
jinja2.defaults.DEFAULT_NAMESPACE["datetime"] = wrap_datetime
jinja2.defaults.DEFAULT_NAMESPACE["timedelta"] = datetime.timedelta
jinja2.defaults.DEFAULT_NAMESPACE["generate_ics"] = generate_ics

# ordinals
jinja2.filters.FILTERS["make_agree_with_number"] = lambda word, n: morph.parse(word)[0].make_agree_with_number(n).word
jinja2.filters.FILTERS["num2text"] = num2text
jinja2.filters.FILTERS["num2ord"] = num2ord
jinja2.filters.FILTERS["num2text_in_text"] = num2text.replace_everything_in_text
jinja2.filters.FILTERS["num2ord_in_text"] = num2ord.replace_everything_in_text
jinja2.filters.FILTERS["money2text"] = lambda amount, currency: money2text(amount, currency)
jinja2.filters.FILTERS["currency2name"] = lambda currency: CURRENCY_CODE_2_NAME_MAP.get(f"{currency}".upper(), currency)

# time
jinja2.filters.FILTERS["add_timedelta"] = add_timedelta
jinja2.filters.FILTERS["timestamp_to_time"] = lambda ts: datetime.datetime.fromtimestamp(ts)
jinja2.filters.FILTERS["strftime"] = lambda datetime, fmt: datetime.strftime(fmt)
jinja2.filters.FILTERS["timestamp_to_date"] = timestamp_to_date

# numbers
jinja2.filters.FILTERS["comma_float"] = lambda x: float(x.replace(",", "."))
jinja2.filters.FILTERS["careful_int"] = lambda x: int(x) if x.is_integer() else x
jinja2.filters.FILTERS["reduce"] = lambda num, reduce_num: int(num) - int(reduce_num)
jinja2.filters.FILTERS["increase"] = lambda num, increase_num: int(num) + int(increase_num)

# str
jinja2.filters.FILTERS["strip"] = str.strip
jinja2.filters.FILTERS["rstrip"] = str.rstrip
jinja2.filters.FILTERS["lstrip"] = str.lstrip
jinja2.filters.FILTERS["title"] = str.title
jinja2.filters.FILTERS["inflect"] = lambda text, required_grammemes: inflect(morph, text, required_grammemes)
jinja2.filters.FILTERS["url_quote"] = quote
jinja2.filters.FILTERS["url_unquote"] = unquote
jinja2.filters.FILTERS["hash_md5"] = lambda s: hashlib.md5(s.encode()).hexdigest()

# lists and sets
jinja2.filters.FILTERS["intersect"] = lambda x, y: set(x) & set(y)
jinja2.filters.FILTERS["difference"] = lambda x, y: set(x) - set(y)
jinja2.filters.FILTERS["co_sort"] = co_sort

# other
jinja2.filters.FILTERS["tojson"] = lambda x: json.dumps(x, ensure_ascii=False)
jinja2.filters.FILTERS["fromjson"] = json.loads
jinja2.filters.FILTERS["any"] = any
jinja2.filters.FILTERS["all"] = all
jinja2.filters.FILTERS["pan2service"] = pan2service
jinja2.filters.FILTERS["shuffle"] = lambda l: random.sample(l, len(l))

# absolutely custom
jinja2.filters.FILTERS["okko_sec2text"] = okko_sec2text

# Base64 encoding-decoding
# Additional padding in decode functions added to prevent 'Invalid padding error' for incorrectly-padded base64 strings
# len(input_string) must be divisible by 4, if not it should be padded with '=' char to match the requirement
# '===' is added to cover all cases, if string ends with '=' it is truncated to the nearest multiplier of 4 (internal impl)
jinja2.filters.FILTERS["b64decode"] = lambda a: base64.b64decode(a + '===')
jinja2.filters.FILTERS["b64encode"] = base64.b64encode
jinja2.filters.FILTERS["urlsafe_b64decode"] = lambda a: base64.urlsafe_b64decode(a + '===')
jinja2.filters.FILTERS["urlsafe_b64encode"] = base64.urlsafe_b64encode
jinja2.filters.FILTERS["tob64urlsafe"] = lambda x: base64.urlsafe_b64encode(bytes(x, 'UTF-8')).decode('utf-8')

# encoding
jinja2.filters.FILTERS["codecs_decode"] = lambda b, encoding='utf-8': codecs.decode(b, encoding=encoding)
jinja2.filters.FILTERS["codecs_encode"] = lambda s, encoding='utf-8': codecs.decode(s, encoding=encoding)

#localization
jinja2.filters.FILTERS["phone_number_ru"] = phone_number_ru
