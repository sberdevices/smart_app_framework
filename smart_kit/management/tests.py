import argparse
import sys
import os
import shutil
import smart_kit

from core.descriptions.descriptions import Descriptions

from smart_kit.management.base import AppCommand
from smart_kit.testing.suite import TestSuite


def define_path(path):
    if os.path.exists(path):
        return path
    folder, _ = os.path.split(sys.argv[0])
    return os.path.join(folder, path)


class TestsCommand(AppCommand):
    TEST_TEMPLATE_PATH = "test_template.json"
    DEFAULT_TEMPLATE_PATH = os.path.join(smart_kit.__path__[0], "template/static/references/test_template.json")
    TEST_EXTENSION = ".json"

    def __init__(self, app_config):
        self.app_config = app_config
        self.parser = argparse.ArgumentParser(description="Tests creating and running.")
        self.parser.add_argument("path", metavar="PATH", type=str, help="Path to directory with tests", action="store")
        self.commands = self.parser.add_mutually_exclusive_group(required=True)
        self.commands.add_argument("--run", dest="run", help="Runs Tests", action="store_true")
        self.commands.add_argument(
            "--gen", dest="gen", help="Create test directory at provided path", action="store_true"
        )

        gen_command = self.parser.add_argument_group("Generating")
        gen_command.add_argument(
            "--update", dest="update", help="Create missing template for scenarios", action="store_true",
        )

    def execute(self, *args, **kwargs):
        namespace = self.parser.parse_args(args)
        if namespace.gen:
            self.generate_tests_folder(namespace.path, namespace.update)
        elif namespace.run:
            self.run_tests(namespace.path)
        else:
            raise Exception("Something going wrong due parsing the args")

    def generate_tests_folder(self, path: str, update=False):
        settings = self.app_config.SETTINGS(
            config_path=self.app_config.CONFIGS_PATH, secret_path=self.app_config.SECRET_PATH,
            references_path=self.app_config.REFERENCES_PATH, app_name=self.app_config.APP_NAME
        )
        resources = self.app_config.RESOURCES(settings.get_source(), self.app_config.REFERENCES_PATH, settings)
        scenario_names = Descriptions(resources.registered_repositories)["scenarios"].keys()
        folder_path = define_path(path)

        try:
            os.mkdir(folder_path)
            print(f"[+] Created tests folder at: {folder_path}")
        except FileExistsError:
            if not update:
                raise
            print(f"[+] Update tests folder at: {folder_path}")

        with open(self.get_test_template_path(), "r") as template_file:
            for scen_name in scenario_names:
                template_file.seek(0)
                new_file_path = os.path.join(folder_path, scen_name + self.TEST_EXTENSION)
                try:
                    with open(new_file_path, "x") as new_test_file:
                        shutil.copyfileobj(template_file, new_test_file)
                        print(f"[+] Created template file {new_file_path}")
                except FileExistsError:
                    if not update:
                        raise

    def run_tests(self, path):
        path = define_path(path)
        if not os.path.exists(path):
            print(f"[!] Tests folder does not found at {path}")
            return

        TestSuite(path, self.app_config).run()

    def get_test_template_path(self):
        path = os.path.join(self.app_config.REFERENCES_PATH, self.TEST_TEMPLATE_PATH)
        if not os.path.exists(path):
            print(f"[!] Template for test file does not found. Expected at path {path}. Using default")
            path = self.DEFAULT_TEMPLATE_PATH
        return path
