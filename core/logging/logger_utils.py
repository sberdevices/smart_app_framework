import logging
import inspect
import core.logging.logger_constants as log_const
from core.logging.masker import LogMasker
import timeout_decorator


MESSAGE_ID_STR = "message_id"
UID_STR = "uid"
LOGGING_UUID = "logging_uuid"
CLASS_NAME = "class_name"


def _make_message(user=None, params=None, cls_name=''):
    message_id = None
    uuid = None
    logging_uuid = None
    params = params or {}
    if user:
        message = user.message
        message_id = message.incremental_id
        uuid = user.id
        logging_uuid = message.logging_uuid
        atr_names = ["channel", "type", "device_channel", "device_channel_version", "device_platform", "group",
                     "device_platform_version", "device_platform_client_type", "csa_profile_id", "test_deploy"]
        for name in atr_names:
            param = getattr(message, name, None)
            if param:
                params[name] = param
    params = LogMasker.mask_structure(params, LogMasker.percent_fix)
    params[UID_STR] = uuid
    params[MESSAGE_ID_STR] = message_id
    params[LOGGING_UUID] = logging_uuid
    params[CLASS_NAME] = cls_name
    return params


app_logger = logging.getLogger(log_const.APP_LOGGER_NAME)


def log(message, user=None, params=None, level="INFO", exc_info=None):
    try:
        level_name = logging.getLevelName(level)
        current_frame = inspect.currentframe()
        previous_frame = current_frame.f_back.f_locals
        instance = previous_frame.get('self', None)
        if instance is not None:
            params = _make_message(user, params, instance.__class__.__name__)
        else:
            params = _make_message(user, params)

        masked_message = LogMasker.mask_structure(message, LogMasker.regular_exp)
        masked_params = LogMasker.mask_structure(params, LogMasker.regular_exp)

        app_logger.log(level_name, masked_message, masked_params, exc_info=exc_info)
    except timeout_decorator.TimeoutError:
        raise
    except:
        app_logger.log(logging.getLevelName("ERROR"), "Failed to write a log. Exception occurred",
                       params, exc_info=True)


# backward naming_compatibility
behaviour_log = log
