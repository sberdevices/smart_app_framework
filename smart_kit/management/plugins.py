import importlib

from core.logging.logger_utils import log


def activate_plugins(app_config, manager):
    for plugin in app_config.PLUGINS:
        try:
            plugin = importlib.import_module(plugin)
        except ImportError as exc:
            log(f"Error due importing {plugin}.\n {exc}. Plugin {plugin} is installed?", level="ERROR")
            continue

        try:
            plugin.on_startup(app_config, manager)
        except AttributeError:
            log(f"Plugin {plugin.__name__} does not have on_startup method", level="ERROR")
            continue
        except Exception as exc:
            log(f"Error due executing {plugin.__name__} plugin.\n {exc}", level="ERROR")
            continue
