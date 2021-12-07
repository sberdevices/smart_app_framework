# coding: utf-8
import socket
import unittest
from collections import OrderedDict
from collections import namedtuple
from unittest.mock import Mock

import scenarios.behaviors.behaviors


class BehaviorsTest(unittest.TestCase):
    def setUp(self):
        self.user = Mock()
        self.user.settings = Mock()
        self.user.settings.app_name = "app_name"
        self.user.local_vars.values = {"test_local_var_key": "test_local_var_value"}
        self.description = Mock()
        self.description.timeout = Mock(return_value=10)
        self.success_action = Mock()
        self.success_action.run = Mock()
        self.fail_action = Mock()
        self.timeout_action = Mock()

        self.description.success_action = self.success_action
        self.description.fail_action = self.fail_action
        self.description.timeout_action = self.timeout_action
        self.descriptions = {"test": self.description}
        self._callback = namedtuple('Callback', 'behavior_id expire_time scenario_id')

    def test_success(self):
        callback_id = "123"
        behavior_id = "test"
        item = {"behavior_id": behavior_id, "expire_time": 2554416000, "scenario_id": None,
                "text_preprocessing_result": {}}
        items = {str(callback_id): item}
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        behaviors.success(callback_id)
        # self.success_action.run.assert_called_once_with(self.user, TextPreprocessingResult({}))
        self.success_action.run.assert_called_once()
        self.assertDictEqual(behaviors.raw, {})

    def test_success_2(self):
        callback_id = "123"
        items = {}
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        behaviors.success(callback_id)
        self.success_action.run.assert_not_called()

    def test_fail(self):
        callback_id = "123"
        behavior_id = "test"
        item = {"behavior_id": behavior_id, "expire_time": 2554416000, "scenario_id": None}
        items = {str(callback_id): item}
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        behaviors.fail(callback_id)
        self.fail_action.run.assert_called_once()
        self.assertDictEqual(behaviors.raw, {})

    def test_timeout(self):
        callback_id = "123"
        behavior_id = "test"
        item = {"behavior_id": behavior_id, "expire_time": 2554416000, "scenario_id": None}
        items = {str(callback_id): item}
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        behaviors.timeout(callback_id)
        self.timeout_action.run.assert_called_once()
        self.assertDictEqual(behaviors.raw, {})

    def test_expire(self):
        callback_id = "123"
        behavior_id = "test"
        item = {"behavior_id": behavior_id, "expire_time": 1548079039, "scenario_id": None}
        items = {str(callback_id): item}
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        behaviors.expire()
        self.assertDictEqual(behaviors.raw, {})

    @unittest.mock.patch.object(scenarios.behaviors.behaviors, "time", return_value=9999999999)
    def test_add_1(self, time):
        items = {}
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        callback_id = "123"
        behavior_id = "test"
        text_preprocessing_result = {}
        behaviors.add(callback_id, behavior_id)
        _time = int(time()) + self.description.timeout(None) + scenarios.behaviors.behaviors.Behaviors.EXPIRATION_DELAY

        exp = OrderedDict(behavior_id=behavior_id, expire_time=_time, scenario_id=None,
                          text_preprocessing_result=text_preprocessing_result,
                          action_params={'local_vars': {'test_local_var_key': 'test_local_var_value'}},
                          hostname=socket.gethostname())
        self.assertDictEqual(behaviors.raw, {callback_id: exp})

    @unittest.mock.patch.object(scenarios.behaviors.behaviors, "time", return_value=9999999999)
    def test_add_2(self, time):
        items = {}
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        callback_id = "123"
        behavior_id = "test"
        scenario_id = "test_scen"
        text_preprocessing_result = {"test_scen": 1}

        behaviors.add(callback_id, behavior_id, scenario_id, text_preprocessing_result)
        _time = int(time()) + self.description.timeout(None) + scenarios.behaviors.behaviors.Behaviors.EXPIRATION_DELAY
        exp = OrderedDict(behavior_id=behavior_id, expire_time=_time, scenario_id=scenario_id,
                          text_preprocessing_result=text_preprocessing_result,
                          action_params={'local_vars': {'test_local_var_key': 'test_local_var_value'}},
                          hostname=socket.gethostname())
        self.assertDictEqual(behaviors.raw, {callback_id: exp})

    def test_check_1(self):
        callback_id = "123"
        behavior_id = "test"
        item = {"behavior_id": behavior_id, "expire_time": 1548079039, "scenario_id": None}
        items = {str(callback_id): item}
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        self.assertTrue(behaviors.check_got_saved_id(behavior_id))

    def test_check_2(self):
        callback_id = "123"
        behavior_id = "test"
        item = {"behavior_id": behavior_id, "expire_time": 1548079039, "scenario_id": None}
        items = {str(callback_id): item}
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        with self.assertRaises(KeyError):
            behaviors.check_got_saved_id("test2")

    def test_check_misstate_1(self):
        callback_id = "123"
        behavior_id = "test"
        scenario_id = "test_scen"
        item = {"behavior_id": behavior_id, "expire_time": 1548079039, "scenario_id": scenario_id}
        items = {str(callback_id): item}
        self.user.last_scenarios = Mock()
        self.user.last_scenarios.last_scenario_name = "test_scen2"
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        self.assertTrue(behaviors.check_misstate(callback_id))

    def test_check_misstate_2(self):
        callback_id = "123"
        behavior_id = "test"
        scenario_id = "test_scen"
        item = {"behavior_id": behavior_id, "expire_time": 1548079039, "scenario_id": scenario_id}
        items = {str(callback_id): item}
        self.user.last_scenarios = Mock()
        self.user.last_scenarios.last_scenario_name = "test_scen"
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        self.assertFalse(behaviors.check_misstate(callback_id))

    def test_raw(self):
        callback_id = "123"
        behavior_id = "test"
        scenario_id = "test_scen"
        text_preprocessing_result = {1: 2}

        item = {"behavior_id": behavior_id, "expire_time": 1548079039, "scenario_id": scenario_id,
                "text_preprocessing_result": text_preprocessing_result}

        items = {str(callback_id): item}
        behaviors = scenarios.behaviors.behaviors.Behaviors(items, self.descriptions, self.user)
        behaviors.initialize()
        expected = OrderedDict(behavior_id=behavior_id, expire_time=1548079039, scenario_id=scenario_id,
                               text_preprocessing_result=text_preprocessing_result, action_params={},
                               hostname=None)
        self.assertEqual(behaviors.raw, {callback_id: expected})
