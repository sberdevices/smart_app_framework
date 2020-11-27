# coding: utf-8
import unittest
from smart_kit.management import smart_kit_manager
import os
import shutil


class ManagementTest2(unittest.TestCase):
    def setUp(self):
        self.test_folder = "any_dir_name"

    def test_smart_kit_manager(self):
        obj1 = smart_kit_manager.SmartKitManager()
        with self.assertRaises(KeyError):
            obj1.default((1, 2, 3))

    def test_version_command(self):
        obj1 = smart_kit_manager.AppCommand()
        with self.assertRaises(NotImplementedError):
            obj1.execute(*(1, 2, 3), **{"d": 4})

    def test_create_app_command_init(self):
        obj1 = smart_kit_manager.CreateAppCommand()
        self.assertTrue(obj1.TEMPLATE_FOLDER == "template")
        self.assertTrue(obj1.extensions == ".py")
        self.assertTrue(hasattr(obj1, 'doc'))


class ManagementTest3(unittest.TestCase):
    def setUp(self):
        self.test_folder = "any_dir_name"

    def tearDown(self):
        shutil.rmtree(os.path.join(os.getcwd(), self.test_folder))

    def test_create_app_command_execute(self):
        obj1 = smart_kit_manager.CreateAppCommand()
        # использует try except - хотя в принципе достаточно проверить что app_name существует
        with self.assertRaises(FileExistsError):
            obj1.execute("")
        # рабочий вариант
        obj1.execute(self.test_folder)
        self.assertTrue(os.path.exists(os.path.join(os.getcwd(), self.test_folder)))
        # проверяем наличие файлов
        self.assertTrue(os.path.exists(os.path.join(os.getcwd(), self.test_folder, "manage.py")))
        self.assertTrue(os.path.exists(os.path.join(os.getcwd(), self.test_folder, "app", "user", "user.py")))
        self.assertTrue(os.path.exists(os.path.join(os.getcwd(), self.test_folder, "static", "references", "forms",
                                                    "hello_form.json")))
