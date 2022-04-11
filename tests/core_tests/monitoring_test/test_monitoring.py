# -*- coding: utf-8 -*-
import unittest

from prometheus_client import Counter, Histogram

from core.monitoring.monitoring import Monitoring
from smart_kit.utils.picklable_mock import PicklableMock


class MonitoringTest(unittest.TestCase):
    def setUp(self):
        self.logger = PicklableMock()
        self.logger.exception = PicklableMock()
        self.config = PicklableMock()
        self.mock_rep = PicklableMock()
        self.monitoring = Monitoring()
        self.monitoring.apply_config({})

    def test_got_message_disabled(self):
        self.monitoring.turn_off()
        event_name = "test_counter"
        counter_item = self.monitoring._monitoring_items[self.monitoring.COUNTER]
        self.assertTrue(counter_item == dict())
        self.monitoring.got_counter(event_name)
        self.assertTrue(event_name not in counter_item)
        self.assertEqual(counter_item.get(event_name), None)

    def test_got_message_enabled(self):
        self.monitoring.turn_on()
        event_name = "test_counter"
        counter_item = self.monitoring._monitoring_items[self.monitoring.COUNTER]
        self.assertTrue(counter_item == dict())
        self.monitoring.got_counter(event_name)
        self.assertTrue(event_name in counter_item)
        self.assertEqual(type(counter_item[event_name]), type(Counter('counter_name', 'counter_name')))

    def test_got_histogram_disabled(self):
        self.monitoring.turn_off()
        event_name = "test_histogram"
        histogram_item = self.monitoring._monitoring_items[self.monitoring.HISTOGRAM]
        self.assertTrue(histogram_item == dict())
        histogram = self.monitoring._got_histogram(event_name)
        self.assertTrue(event_name not in histogram_item)
        self.assertIsNone(histogram)

    def test_got_histogram_enabled(self):
        self.monitoring.turn_on()
        event_name = "test_histogram"
        histogram_item = self.monitoring._monitoring_items[self.monitoring.HISTOGRAM]
        self.assertTrue(histogram_item == dict())
        self.monitoring._got_histogram(event_name)
        histogram_item = self.monitoring._monitoring_items[self.monitoring.HISTOGRAM]
        self.assertTrue(event_name in histogram_item)
        self.assertEqual(type(histogram_item[event_name]), type(Histogram('histogram_name', 'histogram_name')))

    def test_got_histogram_disabled_by_name(self):
        self.monitoring.turn_on()
        self.monitoring.disabled_metrics.append('test_.*')
        self.monitoring.disabled_metrics.append('.*_all')
        for event_name, disabled in [("test_one", True), ("test_two", True),
                                     ("not_a_test", False), ('metric_all', True)]:
            counter_item = self.monitoring._monitoring_items[self.monitoring.COUNTER]
            self.assertTrue(isinstance(counter_item, dict), event_name)
            self.monitoring.got_counter(event_name)
            if disabled:
                self.assertTrue(event_name not in counter_item, event_name)
            else:
                self.assertTrue(event_name in counter_item, event_name)

    def test_monitoring_init(self):
        from core.monitoring.monitoring import monitoring

        class MyCustomMonitoring(Monitoring):
            pass

        monitoring.set_instance(MyCustomMonitoring)
        self.assertEqual(type(monitoring.instance), MyCustomMonitoring)

        monitoring.set_instance(Monitoring)
        self.assertEqual(type(monitoring.instance), Monitoring)

    def test_decorator(self):
        from core.monitoring.monitoring import monitoring

        class MyCustomMonitoring(Monitoring):
            def got_histogram(self, name, description=None):
                def decorator(function):
                    def wrapper(*args, **kwargs):
                        result = function(*args, **kwargs) + " " + name
                        return result

                    return wrapper

                return decorator

        class SomeClass:
            @monitoring.got_histogram("test_histogram")
            def some_method(self):
                return "test"

        obj = SomeClass()
        self.assertEqual(obj.some_method(), "test")

        monitoring.set_instance(MyCustomMonitoring)
        self.assertEqual(obj.some_method(), "test test_histogram")

        monitoring.set_instance(Monitoring)
        self.assertEqual(obj.some_method(), "test")

        self.assertIn('test_histogram', monitoring._monitoring_items[Monitoring.HISTOGRAM].keys())

