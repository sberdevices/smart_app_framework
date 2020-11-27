import sys

from smart_kit.management.base import HelpCommand

from smart_kit.management.smart_kit_manager import SmartKitManager, CreateAppCommand, VersionCommand

if __name__ == "__main__":
    Manager = SmartKitManager()
    Manager.register_command("create_app", CreateAppCommand)
    Manager.register_command("version", VersionCommand)
    Manager.register_command("help", HelpCommand, Manager.commands)
    Manager.execute_from_command_line(sys.argv)
