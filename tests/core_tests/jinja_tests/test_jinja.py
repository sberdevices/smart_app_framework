import datetime
from unittest import TestCase
import core.unified_template.jinja_filters
import jinja2
from core.unified_template.num2ordinal import Num2Ordinal
from core.unified_template.num2text import Num2Text
from core.unified_template.currency2text import Money2Text


class TestJinjaTemplates(TestCase):
    def setUp(self):
        self.num2text = Num2Text()
        self.num2ord = Num2Ordinal()
        self.money2text = Money2Text()

    def test_inflect(self):
        template = jinja2.Template(
            "Поставим слово '{{ word }}' в множественное число, родительный падеж: '{{ word|inflect(['plur', 'gent']) }}'")
        self.assertEqual(
            "Поставим слово 'бутявка' в множественное число, родительный падеж: 'бутявок'",
            template.render({"word": "бутявка"})
        )

    def test_inflect_several_words_with_register(self):
        template = jinja2.Template("{{text|inflect(['loct'])}}")
        self.assertEqual(
            "О золотой карте в Санкт-Петербурге",
            template.render({"text": "О золотая карта в Санкт-Петербурге"})
        )

    def test_make_agree_with_number_1(self):
        template = jinja2.Template("Температура: {{temperature}} {{'градус'|make_agree_with_number(temperature)}}")
        self.assertEqual("Температура: 21 градус", template.render({"temperature": 21}))

    def test_make_agree_with_number_2(self):
        template = jinja2.Template("Температура: {{temperature}} {{'градус'|make_agree_with_number(temperature)}}")
        self.assertEqual("Температура: 25 градусов", template.render({"temperature": 25}))

    def test_comma_float_ordinar_float(self):
        template = jinja2.Template("{{'1.23'|comma_float * 2}}")
        self.assertEqual("2.46", template.render())

    def test_comma_float_comma_float(self):
        template = jinja2.Template("{{'1,23'|comma_float * 2}}")
        self.assertEqual("2.46", template.render())

    def test_careful_int_true_int(self):
        template = jinja2.Template("{{t|careful_int * 2}}")
        self.assertEqual("2", template.render({"t": 1.0}))

    def test_careful_int_false_int(self):
        template = jinja2.Template("{{t|careful_int * 2}}")
        self.assertEqual("2.46", template.render({"t": 1.23}))

    def test_tojson(self):
        template = jinja2.Template("{{t|tojson}}")
        self.assertEqual('{"word": 1, "n": null}', template.render({"t": {"word": 1, "n": None}}))

    def test_fromjson(self):
        template = jinja2.Template("{{t|fromjson}}")
        self.assertEqual("{'word': 1, 'n': None}", template.render({"t": '{"word": 1, "n": null}'}))

    def test_num2text_natural(self):
        template = jinja2.Template("{{t|num2text}} {{'градус'|make_agree_with_number(t|abs)}}")
        self.assertEqual("двадцать один градус", template.render({"t": 21}))

    def test_num2text_real(self):
        template = jinja2.Template("{{t|num2text}} {{'градус'|make_agree_with_number(t|abs)}}")
        self.assertEqual("минус семнадцать с половиной градусов", template.render({"t": -17.5}))

    def test_num2text_usual_number(self):
        self.assertEqual("одиннадцать", self.num2text(11))

    def test_num2text_big_number(self):
        self.assertEqual("сто шестьдесят семь тысяч триста сорок два", self.num2text(167342))

    def test_num2text_frac_number(self):
        self.assertEqual("двенадцать целых тридцать четыре сотых", self.num2text(12.34))

    def test_num2text_half_frac_number(self):
        self.assertEqual("семнадцать с половиной", self.num2text(17.5))

    def test_num2text_m(self):
        self.assertEqual("два", self.num2text(2))

    def test_num2text_f(self):
        self.assertEqual("две", self.num2text(2, "f"))

    def test_num2text_str(self):
        self.assertEqual("два", self.num2text("2"))

    def test_num2text_negative_real(self):
        self.assertEqual("минус две целых шестьдесят семь сотых", self.num2text(-2.67))

    def test_num2ord_gen_neut(self):
        self.assertEqual("восьмого", self.num2ord(8, 'n', 'gent'))

    def test_jinja_num2text_half_frac_number(self):
        template = jinja2.Template("{{t|num2text}} градусов")
        self.assertEqual("семнадцать с половиной градусов", template.render({"t": 17.5}))

    def test_jinja_num2ord_gen_neut(self):
        template = jinja2.Template("{{t|num2ord('n','gent')}} сентября")
        self.assertEqual("восьмого сентября", template.render({"t": 8}))

    def test_jinja_num2ord_nom_neut(self):
        template = jinja2.Template("{{t|num2ord('n')}} сентября")
        self.assertEqual("восьмое сентября", template.render({"t": 8}))

    def test_jinja_num2ord_replace_all_explicit(self):
        template = jinja2.Template("{{t|num2ord_in_text(only_explicit=True)}}")
        self.assertEqual("двадцать пятый день, двадцать шестая ночь, 27 утро",
                         template.render({"t": "25ый день, 26ая ночь, 27 утро"}))

    def test_jinja_num2ord_replace_all_not_explicit(self):
        template = jinja2.Template("{{t|num2ord_in_text(sex='n')}}")
        self.assertEqual("двадцать пятый день, двадцать шестая ночь, двадцать седьмое утро",
                         template.render({"t": "25ый день, 26ая ночь, 27 утро"}))

    def test_jinja_num2text_replace_all(self):
        template = jinja2.Template("{{t|num2text_in_text(sex='f')}}")
        self.assertEqual("три дня, две ночи",
                         template.render({"t": "3 дня, 2 ночи"}))

    def test_jinja_money2text_special_no_frac(self):
        num, cur = 11.0, 'USD'
        expected = "11 долларов США"
        self.assertEqual(expected, self.money2text(num, cur))

    def test_jinja_money2text_special_with_frac(self):
        num, cur = 11.99, 'USD'
        expected = "11 долларов США 99 центов"
        self.assertEqual(expected, self.money2text(num, cur))

    def test_jinja_money2text_regular_with_frac(self):
        num, cur = 1.99, 'TND'
        expected = "1.99 тунисских динаров"
        self.assertEqual(expected, self.money2text(num, cur))

    def test_jinja_money2text_regular_no_frac(self):
        num, cur = 1, 'CNY'
        expected = "1 юань"
        self.assertEqual(expected, self.money2text(num, cur))

    def test_ics(self):
        date = datetime.datetime.now()

        expected = "".join(map(str, [date.year, "{:02d}".format(date.month), "{:02d}".format(date.day)]))
        got = core.unified_template.jinja_filters.generate_ics(date)
        timestring = got.split()[2] #Third row contains date
        self.assertTrue(expected in timestring)

    def test_date_from_timestamp(self):
        tstamp = 0
        expected = datetime.datetime(1970, 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
        got = core.unified_template.jinja_filters.timestamp_to_datetime(tstamp)
        self.assertEqual(expected, got)

    def test_wrap_datetime(self):
        dt = [1, 1, 2019, 0, 0]
        got = core.unified_template.jinja_filters.wrap_datetime(*dt)
        expected = datetime.datetime(day=1, month=1, year=2019, hour=0, minute=0, tzinfo=datetime.timezone.utc)
        self.assertEqual(expected, got)

    def test_add_timedelta(self):
        date = datetime.datetime.now()
        day = 1
        expected = date + datetime.timedelta(days=day)
        self.assertEqual(expected, core.unified_template.jinja_filters.add_timedelta(date, days=day))

    def test_cardtype_visa(self):
        template = jinja2.Template("{{t|pan2service}}")
        result = template.render({"t": "4716333884162944"})
        self.assertEqual("visa", result)

    def test_cardtype_master(self):
        template = jinja2.Template("{{t|pan2service}}")
        result = template.render({"t": "5122185757184370"})
        self.assertEqual("mastercard", result)

    def test_cardtype_maestro(self):
        template = jinja2.Template("{{t|pan2service}}")
        result = template.render({"t": "6762940925503833"})
        self.assertEqual("maestro", result)

    def test_cardtype_amex(self):
        template = jinja2.Template("{{t|pan2service}}")
        result = template.render({"t": "373268674871118"})
        self.assertEqual("amex", result)

    def test_cardtype_mir(self):
        template = jinja2.Template("{{t|pan2service}}")
        result = template.render({"t": "2222 2222 2222 2222 2"})
        self.assertEqual("mir", result)

    def test_cardtype_visa_masked(self):
        template = jinja2.Template("{{t|pan2service}}")
        result = template.render({"t": "471633****2944"})
        self.assertEqual("visa", result)

    def test_cardtype_visa_empty(self):
        template = jinja2.Template("{{t|pan2service}}")
        result = template.render({"t": ""})
        self.assertEqual("None", result)

    def test_cardtype_visa_formatted(self):
        template = jinja2.Template("{{t|pan2service}}")
        result = template.render({"t": "4716 3311 2222 2944"})
        self.assertEqual("visa", result)

    def test_timestamp_to_date_filter(self):
        self.assertEqual(core.unified_template.jinja_filters.timestamp_to_date(1582890903), "28 февраля", "sec")
        self.assertEqual(core.unified_template.jinja_filters.timestamp_to_date(1582890903000), "28 февраля", "ms")
        self.assertEqual(core.unified_template.jinja_filters.timestamp_to_date(1582890903000000), "28 февраля", "mcs")
