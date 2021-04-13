import os

import scenarios.logging.logger_constants as log_const
from core.logging.logger_utils import log
from smart_kit.configs import get_app_config


def create_app():
    os.environ.setdefault("SMART_KIT_APP_CONFIG", "app_config")
    app_config = get_app_config()

    app_name = app_config.APP_NAME
    configs_path, secret_path, settings_cls, references_path = \
        app_config.CONFIGS_PATH, app_config.SECRET_PATH, app_config.SETTINGS, app_config.REFERENCES_PATH

    resources_cls, model_cls, dialogue_manager_cls, main_loop_cls, user_cls, parametrizer_cls = \
        app_config.RESOURCES, app_config.MODEL, app_config.DIALOGUE_MANAGER, app_config.MAIN_LOOP, \
        app_config.USER, app_config.PARAMETRIZER

    log("START SETTINGS CREATE", params={log_const.KEY_NAME: "timings"})
    settings = settings_cls(config_path=configs_path, secret_path=secret_path, references_path=references_path)
    log("FINISHED SETTINGS CREATE", params={log_const.KEY_NAME: "timings"})
    source = settings.get_source()
    log("START RESOURCES CREATE", params={log_const.KEY_NAME: "timings"})
    resource = resources_cls(source, references_path, settings)
    log("FINISHED RESOURCES CREATE", params={log_const.KEY_NAME: "timings"})
    log("START MODEL CREATE", params={log_const.KEY_NAME: "timings"})
    model = model_cls(resource, dialogue_manager_cls, settings, app_name=app_name)
    log("FINISHED MODEL CREATE", params={log_const.KEY_NAME: "timings"})
    log("START MAIN_LOOP CREATE", params={log_const.KEY_NAME: "timings"})
    loop = main_loop_cls(
        model, user_cls, parametrizer_cls, settings
    )
    log("FINISHED MAIN_LOOP CREATE", params={log_const.KEY_NAME: "timings"})
    return loop
