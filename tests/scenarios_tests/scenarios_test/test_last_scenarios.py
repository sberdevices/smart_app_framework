from unittest import TestCase
from unittest.mock import Mock, MagicMock
from scenarios.user.last_scenarios.last_scenarios import LastScenarios


class ScenarioDescription:
    def __init__(self, dict):
        self._dict=dict

    def __contains__(self, item):
        return item in self._dict.keys()

    def __getitem__(self, item):
        return self._dict[item]


class TestLastScenarios(TestCase):

    def setUp(self):
        self.forms_dict = {'pay_phone_scenario':
                                {'fields': {'amount': {'value': 100.0}, 'approve': {'available': True, 'value': True}},
                                 'remove_time': 1506418333}, 'callcenter_scenario': {'remove_time': 2506421370}}

    def remove_item(self, item):
        self.forms_dict.pop(item)

    def test_add_1(self):
        items = ["pay_phone_scenario"]
        forms = MagicMock(name="context_form_mock")
        forms.clear_form = self.remove_item
        user = Mock()
        user.forms = forms

        pay_phone_scenario = Mock()
        pay_phone_scenario.keep_forms_alive = False
        pay_phone_scenario.form_type = "pay_phone_scenario"
        user.descriptions = {"scenarios": ScenarioDescription({"pay_phone_scenario": pay_phone_scenario})}
        last_scenario_description = Mock()
        last_scenario_description.get_count = Mock(return_value=1)
        ls = LastScenarios(items, last_scenario_description, user)
        new_scenario = "callcenter_scenario"
        ls.add(new_scenario, None)
        self.assertSequenceEqual(["callcenter_scenario"], ls.raw)
        self.assertSequenceEqual({"callcenter_scenario": {"remove_time": 2506421370}}, self.forms_dict)

    def test_add_2(self):
        items = ["pay_phone_scenario"]
        forms = MagicMock(name="context_form_mock")
        user = Mock()
        user.forms = forms

        pay_phone_scenario = Mock()
        pay_phone_scenario.keep_forms_alive = False
        user.descriptions = {"scenarios": {"pay_phone_scenario": pay_phone_scenario}}
        last_scenario_description = Mock()
        last_scenario_description.get_count = Mock(return_value=2)
        ls = LastScenarios(items, last_scenario_description, user)
        new_scenario = "callcenter_scenario"
        ls.add(new_scenario, None)
        self.assertSequenceEqual(["pay_phone_scenario", "callcenter_scenario"], ls.raw)
        self.assertSequenceEqual({"pay_phone_scenario":
                                      {"fields": {"amount": {"value": 100.0},
                                                  "approve": {"available": True, "value": True}},
                                       "remove_time": 1506418333},
                                  "callcenter_scenario": {"remove_time": 2506421370}}, self.forms_dict)

    def test_add_3(self):
        items = ["pay_phone_scenario"]
        forms = MagicMock(name="context_form_mock")
        user = Mock()
        user.forms = forms

        pay_phone_scenario = Mock()
        pay_phone_scenario.keep_forms_alive = True
        user.descriptions = {"scenarios": ScenarioDescription({"pay_phone_scenario": pay_phone_scenario})}
        last_scenario_description = Mock()
        last_scenario_description.check = Mock(return_value=True)
        last_scenario_description.get_count = Mock(return_value=1)
        ls = LastScenarios(items, last_scenario_description, user)
        new_scenario = "callcenter_scenario"
        ls.add(new_scenario, None)
        correct_result = {'pay_phone_scenario': {'fields': {'amount': {'value': 100.0}, 'approve': {'available': True,
                                                                                                    'value': True}},
                          'remove_time': 1506418333}, 'callcenter_scenario': {'remove_time': 2506421370}}
        self.assertSequenceEqual(["callcenter_scenario"], ls.raw)
        self.assertSequenceEqual(correct_result, self.forms_dict)

    def test_add_4(self):
        items = ["pay_phone_scenario"]
        forms = MagicMock(name="context_form_mock")
        forms.clear_form = self.remove_item
        user = Mock()
        user.forms = forms

        pay_phone_scenario = Mock()
        pay_phone_scenario.keep_forms_alive = False
        pay_phone_scenario.form_type = "pay_phone_scenario"
        user.descriptions = {"scenarios": ScenarioDescription({"pay_phone_scenario": pay_phone_scenario})}
        last_scenario_description = Mock()
        last_scenario_description.get_count = Mock(return_value=-1)
        ls = LastScenarios(items, last_scenario_description, user)
        new_scenario = "callcenter_scenario"
        ls.add(new_scenario, None)
        correct_result = {'callcenter_scenario': {'remove_time': 2506421370}}
        self.assertSequenceEqual(["callcenter_scenario"], ls.raw)
        self.assertSequenceEqual(correct_result, self.forms_dict)

    def test_clear_all(self):
        items = ["pay_phone_scenario"]
        forms = MagicMock(name="context_form_mock")
        user = Mock()
        user.forms = forms

        pay_phone_scenario = Mock()
        pay_phone_scenario.keep_forms_alive = False
        user.descriptions = {"scenarios": {"pay_phone_scenario": pay_phone_scenario}}

        last_scenario_description = Mock()
        last_scenario_description.check = Mock(return_value=True)
        last_scenario_description.get_count = Mock(return_value=2)
        ls = LastScenarios(items, last_scenario_description, user)
        new_scenario = "callcenter_scenario"
        ls.add(new_scenario, None)
        ls.clear_all()
        self.assertSequenceEqual([], ls.raw)

    def test_get_last_scenario_1(self):
        items = ["pay_phone_scenario1", "pay_phone_scenario2"]
        user = Mock()
        last_scenario_description = Mock()
        ls = LastScenarios(items, last_scenario_description, user)
        self.assertEqual(ls.last_scenario_name, "pay_phone_scenario2")

    def test_get_last_scenario_2(self):
        items = []
        user = Mock()
        last_scenario_description = Mock()
        ls = LastScenarios(items, last_scenario_description, user)
        self.assertIsNone(ls.last_scenario_name)

    def test_expire(self):
        user = Mock()
        user.forms = {"pay_phone_scenario": None}
        pay_phone_scenario = Mock()
        pay_phone_scenario.form_type = "pay_phone_scenario"
        scenarios = ScenarioDescription({"pay_phone_scenario": pay_phone_scenario})
        user.descriptions = {"scenarios": scenarios}
        last_scenario_description = Mock()
        items = ["pay_phone_scenario"]
        ls = LastScenarios(items, last_scenario_description, user)
        ls.expire()
        self.assertSequenceEqual([], ls.raw)