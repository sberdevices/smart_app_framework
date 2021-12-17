import copy
from unittest import TestCase

from core.utils.masking_message import masking


class MaskingTest(TestCase):
    def test_bank_card(self):
        # 'message' in CARD_MASKING_FIELDS
        input_msg = {"message": "Слово до 1234567890123456"}
        expected = {"message": "Слово до ************3456"}
        masking(input_msg)
        self.assertEqual(input_msg, expected)

        input_msg = {"message": "Слово до 1234567890123456 и после"}
        expected = {"message": "Слово до ************3456 и после"}
        masking(input_msg)
        self.assertEqual(input_msg, expected)

        input_msg = {"message": "Склеено1234567890123456"}
        expected = {"message": "Склеено************3456"}
        masking(input_msg)
        self.assertEqual(input_msg, expected)

        # если это поле входит в банковские, но не проходит по регулярке - то не маскируем
        input_msg = {"message": "1234"}
        expected = {"message": "1234"}
        masking(input_msg)
        self.assertEqual(input_msg, expected)

        # маскировка так же применится к банковскому полю внутри коллекции
        input_msg = {'message': {'card': '1234567890123456'}}
        expected = {'message': {'card': '************3456'}}
        masking(input_msg, masking_fields=['token'])
        self.assertEqual(input_msg, expected)

        # если это не баковское поле - то не маскируем
        input_msg = {'here_no_cards': {'no_card': '1234567890123456'}}
        expected = {'here_no_cards': {'no_card': '1234567890123456'}}
        masking(input_msg)
        self.assertEqual(input_msg, expected)

    def test_masking(self):
        input_message = {"refresh_token": '123456'}
        expected = {"refresh_token": '***'}
        masking(input_message)
        self.assertEqual(input_message, expected)

        # все простые типы маскируются как '***'
        input_message = {"refresh_token": {'int': 123, 'str': 'str', 'bool': True}}
        expected = {"refresh_token": {'int': '***', 'str': '***', 'bool': '***'}}
        masking(input_message)
        self.assertEqual(input_message, expected)

        # если маскируемое поле окажется внутри банковского поля - то оно маскируется с заданной вложеностью
        input_msg = {'message': {'token': ['12', ['12', {'data': {'key': '12'}}]]}}
        expected = {'message': {'token': ['***', ['***', '*items-1*collections-1*maxdepth-2*']]}}
        masking(input_msg, masking_fields={'token': 2})
        self.assertEqual(input_msg, expected)

    def test_depth(self):
        # вложенность любой длины не маскируется пока не встретим ключ для маскировки
        masking_fields = ['token']
        depth_level = 0
        input_msg = {'a': {'b': {'c': 1, 'token': '123456'}}}
        expected = {'a': {'b': {'c': 1, 'token': '***'}}}
        masking(input_msg, masking_fields, depth_level)
        self.assertEqual(input_msg, expected)

        # проверка вложенной маскировки
        input_msg = {'token': [12, 12, {'key': [12, 12]}]}

        depth_level = 3
        expected = {'token': ['***', '***', {'key': ['***', '***']}]}
        input_ = copy.deepcopy(input_msg)
        masking(input_, masking_fields, depth_level)
        self.assertEqual(input_, expected)

        depth_level = 2
        expected = {'token': ['***', '***', {'key': '*items-2*collections-0*maxdepth-1*'}]}
        input_ = copy.deepcopy(input_msg)
        masking(input_, masking_fields, depth_level)
        self.assertEqual(input_, expected)

        depth_level = 1
        expected = {'token': ['***', '***', '*items-2*collections-1*maxdepth-2*']}
        input_ = copy.deepcopy(input_msg)
        masking(input_, masking_fields, depth_level)
        self.assertEqual(input_, expected)

        depth_level = 0
        expected = {'token': '*items-4*collections-2*maxdepth-3*'}
        input_ = copy.deepcopy(input_msg)
        masking(input_, masking_fields, depth_level)
        self.assertEqual(input_, expected)

