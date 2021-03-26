# coding: utf-8
import logging

from core.logging.logger_utils import log


def _start_loop(
        app_name,
        configs_path, secret_path, settings_cls, references_path,
        resources_cls, model_cls, dialogue_manager_cls, main_loop_cls, user_cls,
        parametrizer_cls, to_msg_validators, from_msg_validators,
        **kwargs,
):
    log("START SETTINGS CREATE", level="WARNING")
    settings = settings_cls(config_path=configs_path, secret_path=secret_path, references_path=references_path,
                            app_name=app_name)
    log("FINISHED SETTINGS CREATE", level="WARNING")
    source = settings.get_source()
    log("START RESOURCES CREATE", level="WARNING")
    resource = resources_cls(source, references_path, settings)
    log("FINISHED RESOURCES CREATE", level="WARNING")
    log("START MODEL CREATE", level="WARNING")
    model = model_cls(resource, dialogue_manager_cls, settings)
    log("FINISHED MODEL CREATE", level="WARNING")

    log("START MAIN_LOOP CREATE", level="WARNING")
    loop = main_loop_cls(
        model, user_cls, parametrizer_cls, settings, to_msg_validators, from_msg_validators, **kwargs
    )
    log("FINISHED MAIN_LOOP CREATE", level="WARNING")
    loop.run()


def run(app_config):
    log("RUN APP starting", level="WARNING")
    _start_loop(
        app_config.APP_NAME,
        app_config.CONFIGS_PATH, app_config.SECRET_PATH, app_config.SETTINGS, app_config.REFERENCES_PATH,
        app_config.RESOURCES, app_config.MODEL, app_config.DIALOGUE_MANAGER, app_config.MAIN_LOOP, app_config.USER,
        app_config.PARAMETRIZER, app_config.FROM_MSG_VALIDATORS, app_config.TO_MSG_VALIDATORS,
    )
    logging.shutdown()
