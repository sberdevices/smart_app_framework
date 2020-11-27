# coding: utf-8
import unittest
from smart_kit.message import device


class MessageDeviceTest1(unittest.TestCase):
    def test_device1(self):
        obj = device.Device(dict())
        self.assertTrue(obj.value == {})
        self.assertTrue(obj.platform_type == "")
        self.assertTrue(obj.platform_version == "")
        self.assertTrue(obj.surface == "")
        self.assertTrue(obj.surface_version == "")
        self.assertTrue(obj.features == {})
        self.assertTrue(obj.capabilities == {})
        self.assertTrue(obj.additional_info == {})

    def test_device2(self):
        test_dict = {"platformType": "1", "platformVersion": "1", "surface": "1", "surfaceVersion": "1",
                     "features": {1: 1}, "capabilities": {1: 1}, "additionalInfo": {1: 1}}
        obj = device.Device(test_dict)
        self.assertTrue(obj.value == test_dict)
        self.assertTrue(obj.platform_type == "1")
        self.assertTrue(obj.platform_version == "1")
        self.assertTrue(obj.surface == "1")
        self.assertTrue(obj.surface_version == "1")
        self.assertTrue(obj.features == {1: 1})
        self.assertTrue(obj.capabilities == {1: 1})
        self.assertTrue(obj.additional_info == {1: 1})
