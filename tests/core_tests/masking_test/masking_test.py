import copy
from unittest import TestCase

from core.utils.masking_message import masking


class MaskingTest(TestCase):
    def test_bank_card(self):
        # 'message' in CARD_MASKING_FIELDS
        input_msg = {"message": "Слово до 1234567890123456"}
        expected = {"message": "Слово до ************3456"}
        masking(input_msg)
        self.assertEqual(expected, input_msg)

        input_msg = {"message": "Слово до 1234567890123456 и после"}
        expected = {"message": "Слово до ************3456 и после"}
        masking(input_msg)
        self.assertEqual(expected, input_msg)

        input_msg = {"message": "Склеено1234567890123456"}
        expected = {"message": "Склеено************3456"}
        masking(input_msg)
        self.assertEqual(expected, input_msg)

        # если это поле входит в банковские, но не проходит по регулярке - то не маскируем
        input_msg = {"message": "1234"}
        expected = {"message": "1234"}
        masking(input_msg)
        self.assertEqual(expected, input_msg)

        # маскировка так же применится к банковскому полю внутри коллекции
        input_msg = {'message': {'card': '1234567890123456'}}
        expected = {'message': {'card': '************3456'}}
        masking(input_msg, masking_fields=['token'])
        self.assertEqual(expected, input_msg)

        # если это не баковское поле - то не маскируем
        input_msg = {'here_no_cards': {'no_card': '1234567890123456'}}
        expected = {'here_no_cards': {'no_card': '1234567890123456'}}
        masking(input_msg)
        self.assertEqual(expected, input_msg)

        # проверки на целочисленный тип значений
        input_msg = {'message': 1234567890123456}
        expected = {'message': '************3456'}
        masking(input_msg)
        self.assertEqual(expected, input_msg)

        input_msg = {'message': {'card': 1234567890123456}}
        expected = {'message': {'card': '************3456'}}
        masking(input_msg)
        self.assertEqual(expected, input_msg)

        input_msg = {'message': 1234}
        expected = {'message': 1234}
        masking(input_msg)
        self.assertEqual(expected, input_msg)

    def test_masking(self):
        masking_fields = {'spec_token': 2}
        input_msg = {"spec_token": '123456'}
        expected = {"spec_token": '***'}
        masking(input_msg, masking_fields)
        self.assertEqual(expected, input_msg)

        # все простые типы маскируются как '***'
        input_msg = {"spec_token": {'int': 123, 'str': 'str', 'bool': True}}
        expected = {"spec_token": {'int': '***', 'str': '***', 'bool': '***'}}
        masking(input_msg, masking_fields)
        self.assertEqual(expected, input_msg)

        # если маскируемое поле окажется внутри банковского поля - то оно маскируется с заданной вложеностью
        input_msg = {'message': {'spec_token': ['12', ['12', {'data': {'key': '12'}}]]}}
        expected = {'message': {'spec_token': ['***', ['***', '*items-1*collections-1*maxdepth-2*']]}}
        masking(input_msg, masking_fields)
        self.assertEqual(expected, input_msg)

    def test_depth(self):
        # вложенность любой длины не маскируется пока не встретим ключ для маскировки
        masking_fields = ['spec_token']
        depth_level = 0
        input_msg = {'a': {'b': {'c': 1, 'spec_token': '123456'}}}
        expected = {'a': {'b': {'c': 1, 'spec_token': '***'}}}
        masking(input_msg, masking_fields, depth_level)
        self.assertEqual(expected, input_msg)

        # проверка вложенной маскировки
        input_ = {'spec_token': [12, 12, {'key': [12, 12]}]}

        depth_level = 3
        expected = {'spec_token': ['***', '***', {'key': ['***', '***']}]}
        input_msg = copy.deepcopy(input_)
        masking(input_msg, masking_fields, depth_level)
        self.assertEqual(expected, input_msg)

        depth_level = 2
        expected = {'spec_token': ['***', '***', {'key': '*items-2*collections-0*maxdepth-1*'}]}
        input_msg = copy.deepcopy(input_)
        masking(input_msg, masking_fields, depth_level)
        self.assertEqual(expected, input_msg)

        depth_level = 1
        expected = {'spec_token': ['***', '***', '*items-2*collections-1*maxdepth-2*']}
        input_msg = copy.deepcopy(input_)
        masking(input_msg, masking_fields, depth_level)
        self.assertEqual(expected, input_msg)

        depth_level = 0
        expected = {'spec_token': '*items-4*collections-2*maxdepth-3*'}
        input_msg = copy.deepcopy(input_)
        masking(input_msg, masking_fields, depth_level)
        self.assertEqual(expected, input_msg)

    def test_check_set_components(self):
        input_message = {"set": {12, 13, 14}}
        expected = {"set": [12, 13, 14]}
        masking(input_message)
        self.assertEqual(expected, input_message)

        input_message = {"token": {12, 13, 14}}
        expected = {"token": "*items-3*collections-0*maxdepth-1*"}
        masking(input_message)
        self.assertEqual(expected, input_message)

        input_message = {"masked": {12, 13, 14}}
        expected = {"masked": ["***","***","***"]}
        masking(input_message, masking_fields={"masked":2})
        self.assertEqual(expected, input_message)
