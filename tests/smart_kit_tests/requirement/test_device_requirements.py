# coding: utf-8
import unittest
from unittest.mock import Mock
from core.basic_models.requirement import device_requirements


class RequirementTest1(unittest.TestCase):
    def setUp(self):
        self.test_items1 = {"platfrom_type": "any platform"}  # PLATFROM - так задумано?
        self.test_items2 = {"platform_type": "any platform 2"}
        self.test_id = "12345"
        self.test_text_processing_result = Mock('Text processing result')
        self.test_user1 = Mock('User')
        self.test_user1.message = Mock('Message')
        self.test_user1.message.device = Mock('Device')
        self.test_user1.message.device.platform_type = "any platform"
        self.test_user2 = Mock('User')
        self.test_user2.message = Mock('Message')
        self.test_user2.message.device = Mock('Device')
        self.test_user2.message.device.platform_type = "any platform 2"

    def test_platform_type_requirement_init(self):
        obj1 = device_requirements.PlatformTypeRequirement(self.test_items1, self.test_id)
        self.assertTrue(obj1.platfrom_type == self.test_items1["platfrom_type"])
        self.assertTrue(obj1.id == self.test_id)
        with self.assertRaises(KeyError):
            obj2 = device_requirements.PlatformTypeRequirement("", self.test_id)
            self.assertTrue(obj2.items == {})
        with self.assertRaises(KeyError):
            obj3 = device_requirements.PlatformTypeRequirement(self.test_items2, self.test_id)

    def test_platform_type_requirement_check(self):
        obj1 = device_requirements.PlatformTypeRequirement(self.test_items1, self.test_id)
        self.assertTrue(obj1.check(self.test_text_processing_result, self.test_user1))
        self.assertTrue(not obj1.check(self.test_text_processing_result, self.test_user2))


class RequirementTest2(unittest.TestCase):
    def setUp(self):
        self.test_items1 = {"operator": {"amount": "1.11.111"}}
        self.test_items2 = {"operator": {"amount": "AAA.11.111"}}
        self.test_id1 = "12345"

    def test_basic_version_requirement_init(self):
        obj1 = device_requirements.BasicVersionRequirement(self.test_items1, self.test_id1)
        self.assertTrue(obj1._operator == self.test_items1["operator"])
        self.assertTrue(obj1.id == self.test_id1)

