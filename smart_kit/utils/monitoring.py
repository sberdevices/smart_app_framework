from core.logging.logger_constants import KEY_NAME
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring

from prometheus_client import Counter


def _filter_monitoring_msg(msg):
    msg = msg.replace("-", ":")
    return msg


def silence_it(func):
    def wrap(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except:
            log("Metrics: Failed send. Exception occurred.",
                          params={KEY_NAME: "metrics_fail"}, level="ERROR", exc_info=True)
    return wrap


class Metrics:

    @silence_it
    def init_metrics(self, app_name):
        self._get_or_create_counter(_filter_monitoring_msg("{}_load_error".format(app_name)), "Load user data error")
        self._get_or_create_counter(_filter_monitoring_msg("{}_save_error".format(app_name)), "Save user data error")
        self._get_or_create_counter(_filter_monitoring_msg("{}_save_collision".format(app_name)), "Save user data collision")
        self._get_or_create_counter(_filter_monitoring_msg("{}_save_collision_tries_left".format(app_name)),
                                            "Save user data collision all retries left.")
        self._get_or_create_counter(_filter_monitoring_msg("{}_exception".format(app_name)), "Exception in run-time.")
        self._get_or_create_counter(_filter_monitoring_msg("{}_invalid_message".format(app_name)),
                                            "Incoming message validation error.")

    def _get_or_create_counter(self, monitoring_msg, descr, labels=()):
        counter = getattr(self, monitoring_msg, None)
        if not counter:
            counter = Counter(monitoring_msg, descr, labels)
            setattr(self, monitoring_msg, counter)
        return counter

    @silence_it
    def counter_incoming(self, app_name, message_name, handler, user, app_info=None):
        monitoring_msg = _filter_monitoring_msg("{}_incoming".format(app_name))

        c = self._get_or_create_counter(monitoring_msg, "Count of incoming messages",
                                        ['message_name', 'handler', 'project_id', 'system_name', 'application_id',
                                         'app_version_id', 'channel', 'surface'])

        if app_info is not None:
            project_id = app_info.project_id
            system_name = app_info.system_name
            application_id = app_info.application_id
            app_version_id = app_info.app_version_id
        else:
            project_id = system_name = application_id = app_version_id = None
        c.labels(message_name, handler, project_id, system_name,
                 application_id, app_version_id, user.message.channel, user.message.device.surface).inc()

    @silence_it
    def counter_outgoing(self, app_name, message_name, outgoing_message, user):

        monitoring_msg = _filter_monitoring_msg("{}_outgoing".format(app_name))

        c = self._get_or_create_counter(monitoring_msg, "Count of outgoing requests from application.",
                                        ['message_name', 'project_id', 'system_name', 'application_id',
                                         'app_version_id', 'channel', 'surface'])
        app_info = user.message.app_info
        c.labels(message_name, app_info.project_id, app_info.system_name,
                 app_info.application_id,
                 app_info.app_version_id, user.message.channel, user.message.device.surface).inc()

    @silence_it
    def counter_scenario_change(self, app_name, scenario, user):
        monitoring_msg = "{}_scenario_change".format(app_name)

        c = self._get_or_create_counter(monitoring_msg, "Count of scenario change events",
                                        ['scenario', 'project_id', 'system_name', 'application_id',
                                         'app_version_id', 'channel', 'surface'])
        app_info = user.message.app_info
        c.labels(scenario, app_info.project_id, app_info.system_name,
                 app_info.application_id,
                 app_info.app_version_id, user.message.channel, user.message.device.surface).inc()

    @silence_it
    def counter_nothing_found(self, app_name, scenario, user):
        monitoring_msg = "{}_outgoing_nothing_found".format(app_name)
        c = self._get_or_create_counter(monitoring_msg, "Count of scenario nothing found events",
                                        ['scenario', 'project_id', 'system_name', 'application_id',
                                         'app_version_id', 'channel', 'surface'])
        app_info = user.message.app_info
        c.labels(scenario, app_info.project_id, app_info.system_name,
                 app_info.application_id,
                 app_info.app_version_id, user.message.channel, user.message.device.surface).inc()

    @silence_it
    def counter_load_error(self, app_name):
        monitoring_msg = "{}_load_error".format(app_name)
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Load user data error")
        c.inc()

    @silence_it
    def counter_save_error(self, app_name):
        monitoring_msg = "{}_save_error".format(app_name)
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Save user data error")
        c.inc()

    @silence_it
    def counter_save_collision(self, app_name):
        monitoring_msg = "{}_save_collision".format(app_name)
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Save user data collision")
        c.inc()

    @silence_it
    def counter_save_collision_tries_left(self, app_name):
        monitoring_msg = "{}_save_collision_tries_left".format(app_name)
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Save user data collision all retries left.")
        c.inc()

    @silence_it
    def counter_exception(self, app_name):
        monitoring_msg = "{}_exception".format(app_name)
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Exception in run-time.")
        c.inc()

    @silence_it
    def counter_invalid_message(self, app_name):
        monitoring_msg = "{}_invalid_message".format(app_name)
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "Incoming message validation error.")
        c.inc()

    @silence_it
    def counter_behavior_success(self, app_name, request_message_name):
        # 'Number of Success replies on messageName'
        self._behavior_monitoing_by_status(app_name, "success", request_message_name)

    @silence_it
    def counter_behavior_fail(self, app_name, request_message_name):
        # 'Number of Fail replies on messageName'
        self._behavior_monitoing_by_status(app_name, "fail", request_message_name)

    @silence_it
    def counter_behavior_misstate(self, app_name, request_message_name):
        # 'Number of Misstate replies on messageName'
        self._behavior_monitoing_by_status(app_name, "misstate", request_message_name)

    @silence_it
    def counter_behavior_timeout(self, app_name, request_message_name):
        # 'Number of Timeout replies on messageName'
        self._behavior_monitoing_by_status(app_name, "timeout", request_message_name)

    @silence_it
    def counter_behavior_expire(self, app_name, request_message_name):
        # 'Number of expire events on messageName'
        self._behavior_monitoing_by_status(app_name, "expire", request_message_name)

    def _behavior_monitoing_by_status(self, app_name, status, request_message_name):
        monitoring_msg = '{}_callback'.format(app_name)
        c = self._get_or_create_counter(monitoring_msg,
                                        "Count of incoming callback events with request_message_name",
                                        ['request_message_name', 'status'])

        c.labels(request_message_name, status).inc()

    @silence_it
    def counter_mq_long_waiting(self, app_name):
        monitoring_msg = "{}_mq_long_waiting".format(app_name)
        c = self._get_or_create_counter(_filter_monitoring_msg(monitoring_msg), "(Now - creation_time) is greater than threshold")
        c.inc()

    @silence_it
    def sampling_load_time(self, app_name, value):
        monitoring_msg = "{}_load_time".format(app_name)
        monitoring.got_histogram_observe(_filter_monitoring_msg(monitoring_msg), value)

    @silence_it
    def sampling_script_time(self, app_name, value):
        monitoring_msg = "{}_script_time".format(app_name)
        monitoring.got_histogram_observe(_filter_monitoring_msg(monitoring_msg), value)

    @silence_it
    def sampling_save_time(self, app_name, value):
        monitoring_msg = "{}_save_time".format(app_name)
        monitoring.got_histogram_observe(_filter_monitoring_msg(monitoring_msg), value)

    @silence_it
    def sampling_mq_waiting_time(self, app_name, value):
        monitoring_msg = "{}_mq_waiting_time".format(app_name)
        monitoring.got_histogram_observe(_filter_monitoring_msg(monitoring_msg), value)


smart_kit_metrics = Metrics()
