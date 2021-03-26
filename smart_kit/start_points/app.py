# coding: utf-8
import logging

from core.logging.logger_utils import log


def run(app_config):
    log("RUN APP starting", level="WARNING")

    log("START SETTINGS CREATE", level="WARNING")
    settings = app_config.SETTINGS(
        config_path=app_config.CONFIGS_PATH, secret_path=app_config.SECRET_PATH,
        references_path=app_config.REFERENCES_PATH, app_name=app_config.APP_NAME)
    log("FINISHED SETTINGS CREATE", level="WARNING")
    source = settings.get_source()
    log("START RESOURCES CREATE", level="WARNING")
    resource = app_config.RESOURCES(source, app_config.REFERENCES_PATH, settings)
    log("FINISHED RESOURCES CREATE", level="WARNING")
    log("START MODEL CREATE", level="WARNING")
    model = app_config.MODEL(resource, app_config.DIALOGUE_MANAGER, settings)
    log("FINISHED MODEL CREATE", level="WARNING")

    log("START MAIN_LOOP CREATE", level="WARNING")
    loop = app_config.MAIN_LOOP(
        model, app_config.USER, app_config.PARAMETRIZER, settings,
        app_config.TO_MSG_VALIDATORS, app_config.FROM_MSG_VALIDATORS,
    )
    log("FINISHED MAIN_LOOP CREATE", level="WARNING")
    loop.run()
    logging.shutdown()
