import importlib
import os

ENVIRONMENT_VARIABLE = "SMART_KIT_APP_CONFIG"


def set_default(module, name, value):
    if hasattr(module, name):
        return

    setattr(module, name, value)


def get_static_path(app_config_path):
    project_folder, _ = os.path.split(app_config_path)
    static_path = os.path.join(project_folder, "./static")
    return static_path


def get_app_config(environment_variable=ENVIRONMENT_VARIABLE):
    app_config = os.getenv(environment_variable)
    app_config = importlib.import_module(app_config)

    static_path = get_static_path(app_config.__file__)
    set_default(app_config, "STATIC_PATH", static_path)
    set_default(app_config, "CONFIGS_PATH", os.path.join(static_path, "./configs"))
    set_default(app_config, "SECRET_PATH", os.path.join(static_path, "./configs"))
    references_path = os.path.join(static_path, "./references")
    set_default(app_config, "REFERENCES_PATH", references_path)

    # import and init monitoring first - because other classes use a singleton instance of Monitoring
    from core.monitoring.monitoring import Monitoring, monitoring
    set_default(app_config, 'MONITORING', Monitoring)
    monitoring.set_instance(app_config.MONITORING)

    from core.logging.logger_utils import LoggerMessageCreator
    from core.message.from_message import SmartAppFromMessage
    from scenarios.user.parametrizer import Parametrizer
    from scenarios.user.user_model import User
    from smart_kit.configs.settings import Settings
    from smart_kit.models.dialogue_manager import DialogueManager
    from smart_kit.models.smartapp_model import SmartAppModel
    from smart_kit.resources import SmartAppResources
    from smart_kit.start_points.main_loop_http import HttpMainLoop
    from smart_kit.start_points.postprocess import PostprocessMainLoop
    from smart_kit.testing.local import CLInterface
    from smart_kit.text_preprocessing.local_text_normalizer import LocalTextNormalizer
    from smart_kit.utils.cache import JSONCache
    from smart_kit.testing.suite import TestCase

    set_default(app_config, "LOCAL_TESTING", CLInterface)
    set_default(app_config, "TEST_CASE", TestCase)
    set_default(app_config, "NORMALIZER_ADDRESS", "http://127.0.0.1:9000")
    set_default(app_config, "PPS_URL", "")
    set_default(app_config, "NORMALIZER", LocalTextNormalizer())
    set_default(app_config, "USER", User)
    set_default(app_config, "LOGGER_MESSAGE_CREATOR", LoggerMessageCreator)
    set_default(app_config, "MAIN_LOOP", HttpMainLoop)
    set_default(app_config, "POSTPROCESSOR_MAIN_LOOP", PostprocessMainLoop)
    set_default(app_config, "PARAMETRIZER", Parametrizer)
    set_default(app_config, "MODEL", SmartAppModel)
    set_default(app_config, "DIALOGUE_MANAGER", DialogueManager)
    set_default(app_config, "SETTINGS", Settings)
    set_default(app_config, "RESOURCES", SmartAppResources)
    set_default(app_config, "FROM_MSG", SmartAppFromMessage)

    set_default(app_config, "NORMALIZATION_CACHE_TTL", 0)
    set_default(app_config, "NORMALIZATION_CACHE", JSONCache)

    set_default(app_config, "PLUGINS", ())
    set_default(app_config, "TO_MSG_VALIDATORS", ())
    set_default(app_config, "FROM_MSG_VALIDATORS", ())
    set_default(app_config, "AUTO_LISTENING", True)

    set_default(app_config, "STATIC_CLASSIFIERS_PATH", os.path.join(references_path, "./classifiers"))
    set_default(app_config, "STATIC_CLASSIFIERS_DATA_PATH", os.path.join(references_path, "./classifiers_data"))

    # Переменной можно присвоить значение среды, где запускается апп,
    # например: "ift", "uat", "pt", "prod" (это ИФТ, ПСИ, НТ, ПРОМ)
    set_default(app_config, "ENVIRONMENT", None)

    return app_config
