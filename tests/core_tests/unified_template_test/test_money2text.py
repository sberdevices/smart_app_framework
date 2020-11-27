from unittest import TestCase

from core.unified_template.currency2text import Money2Text


class TestMoney2Text(TestCase):
    def setUp(self) -> None:
        self.money2text = Money2Text()

    def test_shows_currency_names(self):
        self.assertEqual('2 рубля', self.money2text(2, "RUR"))
        self.assertEqual('11 долларов США', self.money2text(11.0, 'USD'))
        self.assertEqual('12 евро', self.money2text(12, "EUR"))
        self.assertEqual('2 юаня', self.money2text(2, "CNY"))
        self.assertEqual('2 фунта стерлингов', self.money2text(2, "GBP"))

    def test_shows_diminutives(self):
        self.assertEqual('11 долларов США 11 центов', self.money2text(11.11111111, 'USD'))
        self.assertEqual('14 рублей 5 копеек', self.money2text(14.05, "RUR"))
        self.assertEqual('2 юаня 68 фынь', self.money2text(2.68, "CNY"))
        self.assertEqual('3 фунта стерлингов 40 пенсов', self.money2text(3.4, "GBP"))

    def test_can_inflect_special_cases(self):
        self.assertEqual('1 чешская крона', self.money2text(1, "CZK"))
        self.assertEqual('2 чешские кроны', self.money2text(2, "CZK"))
        self.assertEqual('5 чешских крон 50 геллеров', self.money2text(5.5, "CZK"))

    def test_shows_currency_code_if_currency_unknown(self):
        self.assertEqual('11 XXX', self.money2text(11, 'XXX'))
