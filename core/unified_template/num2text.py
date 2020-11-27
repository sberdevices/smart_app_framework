import re


class Num2Text:
    """
    конвертация чисел в числительные, основано на https://github.com/seriyps/ru_number_to_text
    доделана работа с дробной частью, добавлено больше порядков
    числа по модулю должны быть меньше 1000 дециллионов, дробная часть округляется до 6 порядка
    можно выбирать мужской (m) или женский (f) род (один / одна)
    """
    minus = 'минус'
    units = ('ноль', ('один', 'одна'), ('два', 'две'), 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять')
    teens = ('десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 'пятнадцать', 'шестнадцать',
             'семнадцать', 'восемнадцать', 'девятнадцать')
    tens = (teens, 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто')
    hundreds = ('сто', 'двести', 'триста', 'четыреста', 'пятьсот', 'шестьсот', 'семьсот', 'восемьсот', 'девятьсот')
    orders = (
        (('тысяча', 'тысячи', 'тысяч'), 'f'),
        (('миллион', 'миллиона', 'миллионов'), 'm'),
        (('миллиард', 'миллиарда', 'миллиардов'), 'm'),
        (('триллион', 'триллиона', 'триллионов'), 'm'),
        (('квадриллион', 'квадриллиона', 'квадриллионов'), 'm'),
        (('квинтиллион', 'квинтиллиона', 'квинтиллионов'), 'm'),
        (('секстиллион', 'секстиллиона', 'секстиллионов'), 'm')
    )
    fractionals = (
        ('десятая', 'десятых'), ('сотая', 'сотых'), ('тысячная', 'тысячных'), ('десятитысячная', 'десятитысячных'),
        ('стотысячная', 'стотысячных'), ('милионная', 'милионных')
    )
    fractionals_num = len(fractionals)

    def _thousand(self, rest, sex):
        # Converts numbers from 19 to 999
        prev = 0
        plural = 2
        name = []
        use_teens = 10 <= rest % 100 <= 19
        if not use_teens:
            data = ((self.units, 10), (self.tens, 100), (self.hundreds, 1000))
        else:
            data = ((self.teens, 10), (self.hundreds, 1000))
        for names, x in data:
            cur = int(((rest - prev) % x) * 10 / x)
            prev = rest % x
            if x == 10 and use_teens:
                plural = 2
                name.append(self.teens[cur])
            elif cur == 0:
                continue
            elif x == 10:
                name_ = names[cur]
                if isinstance(name_, tuple):
                    name_ = name_[0 if sex == 'm' else 1]
                name.append(name_)
                if 2 <= cur <= 4:
                    plural = 1
                elif cur == 1:
                    plural = 0
                else:
                    plural = 2
            else:
                name.append(names[cur - 1])
        return plural, name

    def int2text(self, num: int, sex='m'):
        if num == 0:
            return self.units[0]
        main_units = (('', '', ''), sex)
        _orders = (main_units,) + self.orders
        rest = abs(num)
        ord = 0
        name = []
        while rest > 0:
            plural, nme = self._thousand(rest % 1000, _orders[ord][1])
            if nme or ord == 0:
                name.append(_orders[ord][0][plural])
            name += nme
            rest = rest // 1000
            ord += 1
        if num < 0:
            name.append(self.minus)
        name.reverse()
        return ' '.join(name).strip()

    def replace_everything_in_text(self, text, sex='m'):
        return re.sub(
            pattern="[+-]?\d+(?:\.\d+)?",
            repl=lambda x: " {} ".format(self(float(x.group()), sex=sex)),
            string=" {} ".format(text)
        ).strip().replace("  ", " ")

    def __call__(self, num, sex='m'):
        num = float(num)
        num = round(num, self.fractionals_num)
        int_num = int(num)
        if int_num == num:
            return self.int2text(num, sex)
        frac = int(str(round(abs(num) - abs(int_num), self.fractionals_num))[2:])
        if frac == 0:
            return self.int2text(round(num), sex)
        if frac == 5:
            return self.int2text(int_num, sex) + " с половиной"
        return "{} {} {} {}".format(
            self.int2text(int_num, 'f'),
            "целая" if (int_num % 10 == 1) and (int_num % 100 != 11) else "целых",
            self.int2text(frac, 'f'),
            self.fractionals[len(str(frac)) - 1][0 if ((frac % 10 == 1) and (frac % 100 != 11)) else 1]
        )


if __name__ == '__main__':
    num2text = Num2Text()
    # demo
    t = "На улице -2 градуса. Битрикс24. Круассанам 7дней"
    print("Проверим режим замены вхождений по всему тексту: \"{}\"".format(t))
    print(num2text.replace_everything_in_text(t))
    print()

    for t in [11, 167342, 17.5, 12.34, -2.67]:
        r = num2text(t, 'm')
        print(">", t)
        print(r)
    print(">", 22)
    print(num2text(22, 'm'))
    print(">", 22)
    print(num2text(22, 'f'))
    # interactive
    while True:
        t = float(input("> "))
        r = num2text(t, 'm')
        print(r)
