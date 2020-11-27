from core.names import field


def get_callback_action_params(user):
    callback_id = user.message.callback_id
    action_params = user.behaviors.get_callback_action_params(callback_id) or {}
    return action_params


def set_debug_info(app_name, action_params, error):
    saved_debug_info = action_params.setdefault(field.DEBUG_INFO, {})
    dp_debug_info = saved_debug_info.setdefault(app_name, [])
    dp_debug_info.append({"error": error, "status": "{}_error".format(app_name)})

