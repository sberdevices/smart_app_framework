# coding: utf-8
import time

from unittest import TestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.field import field_models, QuestionField
from scenarios.scenario_models.forms.form import form_models, Form
from scenarios.scenario_models.forms.forms import Forms


class MockDescription:
    def __init__(self, id, check_expired, fields=None):
        fields = fields or {}
        self.id = id
        self.check_expired = check_expired
        self.lifetime = 5
        self.valid = True
        self.fields = fields
        self.keep_forms_alive = False
        self.form_type = id


class MockDescriptions:
    def __init__(self, items, *args, **kwargs):
        self.items = items

    def __getitem__(self, key):
        return self.items[key]

    def get(self, key):
        return self.items.get(key)

    def __contains__(self, key):
        return key in self.items


class MockField:
    def __init__(self, id):
        self.id = id
        self.available = True
        self.need_load_context = False
        self.default_value = None


class MockForm:
    def __init__(self, value, description, user):
        self.value = value
        self.description = description

    def check_expired(self):
        return self.description.check_expired

    @property
    def raw(self):
        return self.value


class FormsTest(TestCase):

    def setUp(self):
        self.mock_0 = {}
        self.mock_1 = {'sbm_credit': {'fields': {'amount': {'value': 100.0},
                                                 'currency': {"required": True,
                                                              "filler": {"type": "currency_first"},
                                                              "questions": [{"type": "external",
                                                                             "action": "sbm_currency_question"}]
                                                              }},
                                      'remove_time': 1506418333},
                       'Turn_on_MB': {'remove_time': 2506421370}}

    def test_raw(self):
        user = Mock()
        forms = Forms(self.mock_1, {"sbm_credit": Mock(), "Turn_on_MB": Mock()}, user)
        expected_dict = {'sbm_credit': {'fields': {'amount': {'value': 100.0},
                                                   'currency': {"required": True,
                                                                "filler": {"type": "currency_first"},
                                                                "questions": [{"type": "external",
                                                                               "action": "sbm_currency_question"}]
                                                                }},
                                        'remove_time': 1506418333},
                         'Turn_on_MB': {'remove_time': 2506421370}}
        self.assertDictEqual(forms.raw, expected_dict)

    def test_new(self):
        user = Mock()
        form_models[MockDescription] = Form
        description_MB = MockDescription('Turn_on_MB', False)
        description_credit = MockDescription('sbm_credit', False)
        description_off_MB = MockDescription('Turn_off_MB', False)
        descriptions = {'Turn_on_MB': description_MB, 'sbm_credit': description_credit,
                        'Turn_off_MB': description_off_MB}
        forms = Forms(self.mock_1, descriptions, user)
        form = forms.new('Turn_off_MB')
        ts = int(time.time()) + form.description.lifetime
        expected_dict = {'sbm_credit': {'fields': {'amount': {'value': 100.0},
                                                   'currency': {"required": True,
                                                                "filler": {"type": "currency_first"},
                                                                "questions": [{"type": "external",
                                                                               "action": "sbm_currency_question"}]
                                                                }},
                                        'remove_time': 1506418333},
                         'Turn_on_MB': {'remove_time': 2506421370},
                         'Turn_off_MB': {'remove_time': ts}}
        self.assertDictEqual(forms.raw, expected_dict)

    def test_remove(self):
        user = Mock()
        forms = Forms(self.mock_1, {"sbm_credit": Mock(), "Turn_on_MB": Mock()}, user)
        forms.remove_item("sbm_credit")
        expected_dict = {"Turn_on_MB": {'remove_time': 2506421370}}
        self.assertDictEqual(forms.raw, expected_dict)

    def test_expire(self):
        user = Mock()
        form_models[MockDescription] = MockForm
        description_MB = MockDescription("Turn_on_MB", False)
        description_credit = MockDescription("sbm_credit", True)
        descriptions = {"Turn_on_MB": description_MB, "sbm_credit": description_credit}
        forms = Forms(self.mock_1, descriptions, user)
        forms.expire()
        expected_dict = {"Turn_on_MB": {'remove_time': 2506421370}}
        self.assertDictEqual(forms.raw, expected_dict)

    def test_expire0(self):
        user = Mock()
        form = Mock()
        form.check_expired = False
        form_models[MockDescription] = MockForm
        description_MB = MockDescription("Turn_on_MB", True)
        description_credit = MockDescription("sbm_credit", True)
        descriptions = {"Turn_on_MB": description_MB, "sbm_credit": description_credit}
        forms = Forms(self.mock_1, descriptions, user)
        forms.expire()
        expected_dict = {}
        self.assertDictEqual(forms.raw, expected_dict)

    def test_clear(self):
        user = Mock()
        forms = Forms(self.mock_1, {"mock_descr": Mock()}, user)
        forms.clear_all()
        expected_dict = {}
        self.assertDictEqual(forms.raw, expected_dict)

    def test_collect_form_fields(self):
        user = Mock()
        form_models[MockDescription] = Form
        field_models[MockField] = QuestionField
        field1 = MockField("amount")
        field2 = MockField("currency")
        fields_descriptions = {"amount": field1, "currency": field2}
        description_MB = MockDescription('Turn_on_MB', False, fields_descriptions)
        description_credit = MockDescription('sbm_credit', False, fields_descriptions)
        description_off_MB = MockDescription('Turn_off_MB', False, fields_descriptions)
        _descriptions = {'Turn_on_MB': description_MB, 'sbm_credit': description_credit,
                        'Turn_off_MB': description_off_MB}
        descriptions = MockDescriptions(_descriptions)
        forms = Forms(self.mock_1, descriptions, user)
        result = forms.collect_form_fields()
        expected_fields = set(self.mock_1.keys())
        self.assertSetEqual(set(result.keys()), expected_fields)

    def test_clear_form(self):
        expected_result = {'sbm_credit': {'fields': {'amount': {'value': 100.0},
                                                     'currency': {'filler': {'type': 'currency_first'},
                                                                  'questions': [ {'action': 'sbm_currency_question',
                                                                                  'type': 'external'} ],
                                                                  'required': True}},
                                          'remove_time': 1506418333}}
        description_MB = MockDescription('Turn_on_MB', False)
        description_credit = MockDescription('sbm_credit', False)
        description_off_MB = MockDescription('Turn_off_MB', False)
        descriptions = {"scenarios": MockDescriptions({'Turn_on_MB': description_MB,
                                                       'sbm_credit': description_credit,
                                                       'Turn_off_MB': description_off_MB}),
                        "forms": MockDescriptions({'Turn_on_MB': description_MB,
                                                       'sbm_credit': description_credit,
                                                       'Turn_off_MB': description_off_MB})
                        }
        user = Mock()
        user.descriptions = descriptions
        forms = Forms(self.mock_1, descriptions["forms"], user)
        user.forms = forms
        forms.clear_form("Turn_on_MB")
        self.assertEqual(expected_result, user.forms.raw)
