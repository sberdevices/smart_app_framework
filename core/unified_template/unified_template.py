import json
from copy import copy
import jinja2
from distutils.util import strtobool

import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring

UNIFIED_TEMPLATE_TYPE_NAME = "unified_template"


def bool_loader(val):
    return bool(strtobool(val))


class UnifiedTemplate:
    loaders = {
        "str": str,
        "int": int,
        "float": float,
        "bool": bool_loader,
        "json": json.loads,
    }

    def __init__(self, input):
        self.input = input
        if isinstance(input, str):
            self.template = jinja2.Template(input)
            self.loader = UnifiedTemplate.loaders["str"]
            self.support_templates = dict()
        elif isinstance(input, dict):
            if input.get("type") != UNIFIED_TEMPLATE_TYPE_NAME:
                raise Exception("template must be string or dict with type='{}'".format(UNIFIED_TEMPLATE_TYPE_NAME))
            self.template = jinja2.Template(input["template"])
            self.loader = UnifiedTemplate.loaders[input.get("loader", "str")]
            self.support_templates = {k: UnifiedTemplate(t) for k, t in input.get("support_templates", dict()).items()}
        else:
            raise Exception("template must be string or dict with type='{}'".format(UNIFIED_TEMPLATE_TYPE_NAME))

    def render(self, *args, **kwargs):
        params_dict = dict(*args, **kwargs)
        try:
            result = self.silent_render(params_dict)
        except Exception:
            log("Failed to render template: %(template)s with params {} ".format(str(params_dict)),
                params={log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE,
                          "template": str(self.input)},
                level="ERROR",
                exc_info=True)
            monitoring.got_counter("core_jinja_template_error")
            raise
        return result

    def silent_render(self, params_dict):
        if self.support_templates:
            changed_params_dict = copy(params_dict)
            for support_key, support_template in self.support_templates.items():
                changed_params_dict[support_key] = support_template.render(changed_params_dict)
        else:
            changed_params_dict = params_dict
        if changed_params_dict:
            result = self.template.render(changed_params_dict)
        else:
            result = self.template.render()
        if self.loader != str:
            result = self.loader(result)
        return result

    def __str__(self):
        return str(self.input)
