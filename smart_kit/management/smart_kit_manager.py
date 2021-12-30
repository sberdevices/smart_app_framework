import os
import shutil

import smart_kit
from smart_kit.management.base import Manager, AppCommand


class SmartKitManager(Manager):
    def default(self, argv):
        return self.execute_command("help", *argv[2:])


class VersionCommand(AppCommand):
    def execute(self, *args, **kwargs):
        print(smart_kit.__version__)


class CreateAppCommand(AppCommand):
    """
        Create app folder at given path.
    """

    TEMPLATE_FOLDER = "template"

    def __init__(self, extensions: tuple = None):
        if extensions:
            self.extensions = extensions
        else:
            self.extensions = (".py", ".yml")

    def execute(self, *args, **kwargs):
        app_name = args[0]
        new_app_path = os.path.join(os.getcwd(), app_name)
        try:
            os.makedirs(new_app_path)
        except FileExistsError:
            raise
        template_dir = os.path.join(smart_kit.__path__[0], self.TEMPLATE_FOLDER)
        prefix_length = len(template_dir) + 1
        for root, dirs, files in os.walk(template_dir):

            relative_dir = root[prefix_length:]

            if relative_dir:
                target_dir = os.path.join(new_app_path, relative_dir)
                os.makedirs(target_dir, exist_ok=True)

            for filename in files:
                old_path = os.path.join(root, filename)
                new_path = os.path.join(
                    new_app_path, relative_dir, filename.replace("-tpl", "") if "-tpl" in filename else filename)
                if new_path.endswith(self.extensions):
                    with open(old_path, encoding='utf-8') as template_file:
                        content = template_file.read()
                    content = content.replace("{{app_name}}", app_name)
                    with open(new_path, 'w', encoding='utf-8') as new_file:
                        new_file.write(content)
                else:
                    shutil.copyfile(old_path, new_path)

        print(
            f"{new_app_path} - app created"
        )
