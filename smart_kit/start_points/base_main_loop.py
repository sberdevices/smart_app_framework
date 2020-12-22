# coding=utf-8

import signal

import scenarios.logging.logger_constants as log_const
from core.db_adapter.db_adapter import DBAdapterException
from core.db_adapter.db_adapter import db_adapter_factory
from core.jaeger_custom_client.jaeger_config import ExtendedConfig
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring
from core.monitoring.prometheus_web_handler import RootResource
from core.monitoring.twisted_server import TwistedServer
from smart_kit.utils.monitoring import smart_kit_metrics


class BaseMainLoop:

    def __init__(self, model, user_cls, parametrizer_cls, settings, *args, **kwargs):
        log("%(class_name)s.__init__ started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                                  "class_name": self.__class__.__name__})
        try:
            signal.signal(signal.SIGINT, self.stop)
            signal.signal(signal.SIGTERM, self.stop)
            self.settings = settings
            self.app_name = self.settings.app_name
            self.model = model
            self.user_cls = user_cls
            self.parametrizer_cls = parametrizer_cls
            self.db_adapter = self.get_db()
            self.is_work = True

            template_settings = self.settings["template_settings"]

            save_tries = template_settings.get("user_save_collisions_tries", 0)

            self.user_save_check_for_collisions = True if save_tries > 0 else False
            self.user_save_collisions_tries = max(save_tries, 1)

            self.health_check_server = self._create_health_check_server(template_settings)
            self.tracer = self._create_jaeger_tracer(template_settings)
            if not template_settings["monitoring"].get("enabled"):
                monitoring.turn_off()
            else:
                smart_kit_metrics.init_metrics(app_name=self.app_name)

            log("%(class_name)s.__init__ completed.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                                        "class_name": self.__class__.__name__})
        except:
            log("%(class_name)s.__init__ exception.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                                        "class_name": self.__class__.__name__},
                          level="ERROR", exc_info=True)
            raise

    def get_db(self):
        db_adapter = db_adapter_factory(self.settings["template_settings"].get("db_adapter", {}))
        if db_adapter.IS_ASYNC:
            raise Exception(
                f"Async adapter {db_adapter.__class__.__name__} doesnt compare with {self.__class__.__name__}"
            )
        db_adapter.connect()
        return db_adapter

    def _generate_answers(self, user, commands, message, **kwargs):
        raise NotImplementedError

    def _create_health_check_server(self, settings):
        health_check_server = None
        if settings["health_check"].get("enabled"):
            log("Init health_check monitoring started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE})
            health_check = settings["health_check"]
            health_check_server = TwistedServer(
                health_check["port"],
                health_check["interface"],
                RootResource,
                settings["environment"] in health_check.get("debug_envs", [])
            )
        return health_check_server

    def _create_jaeger_tracer(self, template_settings):
        jaeger_config = template_settings["jaeger_config"]
        config = ExtendedConfig(config=jaeger_config, service_name=self.app_name,
                                validate=True)
        tracer = config.initialize_tracer()
        return tracer

    def load_user(self, db_uid, message):
        db_data = None
        load_error = False
        try:
            db_data = self.db_adapter.get(db_uid)
        except (DBAdapterException, ValueError):
            log("Failed to get user data", params={log_const.KEY_NAME: log_const.FAILED_DB_INTERACTION,
                                                   log_const.REQUEST_VALUE: str(message.value)}, level="ERROR")
            load_error = True
            smart_kit_metrics.counter_load_error(self.app_name)
        return self.user_cls(
            message.uid,
            message=message,
            db_data=db_data,
            settings=self.settings,
            descriptions=self.model.scenario_descriptions,
            parametrizer_cls=self.parametrizer_cls,
            load_error=load_error
        )

    def save_user(self, db_uid, user, message):
        no_collisions = True
        if user.do_not_save:
            log("User %(uid)s will not saved", user=user, params={"uid": user.id,
                                                                  log_const.KEY_NAME: "user_will_not_saved"})
        else:

            no_collisions = True
            try:
                str_data = user.raw_str
                log("Saving User %(uid)s. Serialized utf8 json length is %(user_length)s symbols.", user=user,
                    params={"uid": user.id,
                            log_const.KEY_NAME: "user_save",
                            "user_length": len(str_data)})
                if user.initial_db_data and self.user_save_check_for_collisions:
                    no_collisions = self.db_adapter.replace_if_equals(db_uid,
                                                                      sample=user.initial_db_data,
                                                                      data=str_data)
                else:
                    self.db_adapter.save(db_uid, str_data)
            except (DBAdapterException, ValueError):
                log("Failed to set user data", params={log_const.KEY_NAME: log_const.FAILED_DB_INTERACTION,
                                                       log_const.REQUEST_VALUE: str(message.value)}, level="ERROR")
                smart_kit_metrics.counter_save_error(self.app_name)
            if not no_collisions:
                smart_kit_metrics.counter_save_collision(self.app_name)
        return no_collisions

    def run(self):
        raise NotImplementedError

    def stop(self, signum, frame):
        raise NotImplementedError
