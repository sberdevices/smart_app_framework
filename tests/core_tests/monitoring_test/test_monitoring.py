# -*- coding: utf-8 -*-
import unittest
from unittest.mock import Mock
from prometheus_client import Counter, Histogram

from core.monitoring.monitoring import Monitoring


class MonitoringTest1(unittest.TestCase):
    def setUp(self):
        self.logger = Mock()
        self.logger.exception = Mock()
        self.config = Mock()
        self.mock_rep = Mock()
        self.monitoring = Monitoring()

    def test_got_message_disabled(self):
        self.monitoring.turn_off()
        self.monitoring._monitoring_items[ self.monitoring.COUNTER ] = {}
        event_name = "test_counter"
        counter_item = self.monitoring._monitoring_items[ self.monitoring.COUNTER ]
        self.assertTrue(counter_item == dict())
        counter = self.monitoring.got_histogram(event_name)
        self.assertTrue(event_name not in counter_item)
        self.assertIsNone(counter)

    def test_got_message_enabled(self):
        self.monitoring.turn_on()
        self.monitoring._monitoring_items[ self.monitoring.COUNTER ] = {}
        event_name = "test_counter"
        counter_item = self.monitoring._monitoring_items[ self.monitoring.COUNTER ]
        self.assertTrue(counter_item == dict())
        self.monitoring.got_counter(event_name)
        self.assertTrue(event_name in counter_item)
        self.assertEqual(type(counter_item[ event_name ]), type(Counter('counter_name', 'counter_name')))

    def test_got_histogram_disabled(self):
        self.monitoring.turn_off()
        self.monitoring._monitoring_items[ self.monitoring.HISTOGRAM ] = {}
        event_name = "test_histogram"
        histogram_item = self.monitoring._monitoring_items[ self.monitoring.HISTOGRAM ]
        self.assertTrue(histogram_item == dict())
        histogram = self.monitoring.got_histogram(event_name)
        self.assertTrue(event_name not in histogram_item)
        self.assertIsNone(histogram)

    def test_got_histogram_enabled(self):
        self.monitoring.turn_on()
        self.monitoring._monitoring_items[self.monitoring.HISTOGRAM] = {}
        event_name = "test_histogram"
        histogram_item = self.monitoring._monitoring_items[self.monitoring.HISTOGRAM]
        self.assertTrue(histogram_item == dict())
        self.monitoring.got_histogram(event_name)
        histogram_item = self.monitoring._monitoring_items[self.monitoring.HISTOGRAM]
        self.assertTrue(event_name in histogram_item)
        self.assertEqual(type(histogram_item[event_name]), type(Histogram('histogram_name', 'histogram_name')))
