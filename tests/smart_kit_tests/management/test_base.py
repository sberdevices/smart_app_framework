# coding: utf-8
import unittest
from unittest.mock import Mock
from smart_kit.management import base


class MyCommand:
    def __init__(self, command_):
        self.executer = command_

    def execute(self, *args, **kwargs):
        return self.executer(*args, **kwargs)


class ManagementTest1(unittest.TestCase):
    def setUp(self):
        self.test_command = {"any command": ""}

    def test_app_command(self):
        with self.assertRaises(NotImplementedError):
            obj1 = base.AppCommand()
            obj1.execute((1, 2,), {"a": 1, "b": 2})

    def test_help_command_init(self):
        obj1 = base.HelpCommand(self.test_command)
        self.assertTrue(obj1._commands == self.test_command)

    def test_help_command_execute(self):
        obj1 = base.HelpCommand(self.test_command)
        # сценарий первый - not arg
        obj1.execute(tuple())
        # сценарий второй - len(arg) >= 2
        with self.assertRaises(ValueError):
            obj1.execute((1, 2), {})
        with self.assertRaises(ValueError):
            obj1.execute((1,), {})
        # сценарий третий - без включения
        obj1.execute(("bad command",))
        # сценарий четвёртый - с включением
        obj1.execute(("any command",))

    def test_manager_init(self):
        obj1 = base.Manager()
        self.assertTrue(obj1.commands == {})

    def test_manager_register_command(self):
        obj1 = base.Manager()
        obj1.register_command("str to int", MyCommand, int)
        self.assertTrue("str to int" in obj1.commands)

    def test_manager_execute_command(self):
        obj1 = base.Manager()
        obj1.register_command("str to int", MyCommand, int)
        obj1.execute_command("str to int", "221")
        with self.assertRaises(KeyError):
            obj1.execute_command("str to float", 2.88)

    def test_manager_execute_from_command_line(self):
        obj1 = base.Manager()
        obj1.register_command("str to int", MyCommand, int)
        # Случай 1: len(args) <= 1
        obj1.execute_from_command_line(('star point',))
        # Случай 2: имени нет в словаре команд
        obj1.execute_from_command_line(('star point', "str to float"))
        # Случай 3: имя есть в словаре команд
        self.assertTrue(obj1.execute_from_command_line(('star point', 'str to int', '222')) == 222)
