# coding=utf-8
import json
import time
from collections import namedtuple

from confluent_kafka.cimpl import KafkaException
from lazy import lazy

import scenarios.logging.logger_constants as log_const
from core.jaeger_custom_client import jaeger_utils
from core.jaeger_custom_client import kafka_codec as jaeger_kafka_codec
from core.logging.logger_utils import log, MESSAGE_ID_STR
from core.message.from_message import SmartAppFromMessage
from core.model.heapq.heapq_storage import HeapqKV
from core.mq.kafka.kafka_consumer import KafkaConsumer
from core.mq.kafka.kafka_publisher import KafkaPublisher
from core.utils.stats_timer import StatsTimer
from smart_kit.compatibility.commands import combine_commands
from smart_kit.message.smartapp_to_message import SmartAppToMessage
from smart_kit.names import message_names
from smart_kit.request.kafka_request import SmartKitKafkaRequest
from smart_kit.start_points.base_main_loop import BaseMainLoop
from smart_kit.utils.monitoring import smart_kit_metrics


def _enrich_config_from_secret(kafka_config, secret_config):
    for key in kafka_config:
        if secret_config.get(key):
            kafka_config[key]["consumer"]["conf"].update(secret_config[key]["consumer"]["conf"])
            kafka_config[key]["publisher"]["conf"].update(secret_config[key]["publisher"]["conf"])
    return kafka_config


class MainLoop(BaseMainLoop):

    def __init__(self, model, user_cls, parametrizer_cls, settings, *args, **kwargs):
        super().__init__(model, user_cls, parametrizer_cls, settings, *args, **kwargs)
        log("%(class_name)s.__init__ started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                        "class_name": self.__class__.__name__})
        try:
            kafka_config = _enrich_config_from_secret(
                settings["kafka"]["template-engine"], settings.get("secret_kafka", {})
            )

            consumers = {}
            publishers = {}
            log(
                "%(class_name)s START CONSUMERS/PUBLISHERS CREATE",
                params={"class_name": self.__class__.__name__}, level="WARNING"
            )
            for key, config in kafka_config.items():
                if config.get("consumer"):
                    consumers.update({key: KafkaConsumer(kafka_config[key])})
                if config.get("publisher"):
                    publishers.update({key: KafkaPublisher(kafka_config[key])})
            log(
                "%(class_name)s FINISHED CONSUMERS/PUBLISHERS CREATE",
                params={"class_name": self.__class__.__name__}, level="WARNING"
            )

            self.settings = settings
            self.app_name = self.settings.app_name
            self.model = model
            self.user_cls = user_cls
            self.parametrizer_cls = parametrizer_cls
            self.consumers = consumers
            for key in self.consumers:
                self.consumers[key].subscribe()
            self.publishers = publishers
            self.behaviors_timeouts_value_cls = namedtuple('behaviors_timeouts_value',
                                                           'db_uid, callback_id, mq_message, kafka_key')
            self.behaviors_timeouts = HeapqKV(value_to_key_func=lambda val: val.callback_id)
            log("%(class_name)s.__init__ completed.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__})
        except:
            log("%(class_name)s.__init__ exception.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__},
                level="ERROR", exc_info=True)
            raise

    def run(self):
        log("%(class_name)s.run started", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                  "class_name": self.__class__.__name__})
        while self.is_work:
            self.iterate_behavior_timeouts()
            for kafka_key in self.consumers:
                self.iterate(kafka_key)

            if self.health_check_server:
                self.health_check_server.iterate()

        log("Stopping Kafka handler", level="WARNING")
        for kafka_key in self.consumers:
            self.consumers[kafka_key].close()
            log("Kafka consumer connection is closed", level="WARNING")
            self.publishers[kafka_key].close()
            log("Kafka publisher connection is closed", level="WARNING")
        log("Kafka handler is stopped", level="WARNING")

    def _generate_answers(self, user, commands, message, **kwargs):
        topic_key = kwargs["topic_key"]
        kafka_key = kwargs["kafka_key"]
        answers = []
        commands = commands or []

        commands = combine_commands(commands, user)

        for command in commands:
            request = SmartKitKafkaRequest(id=None, items=command.request_data)
            request.update_empty_items({"topic_key": topic_key, "kafka_key": kafka_key})
            answer = SmartAppToMessage(command=command, message=message, request=request,
                                       masking_fields=self.masking_fields)
            answers.append(answer)

            smart_kit_metrics.counter_outgoing(self.app_name, command.name, answer, user)

        return answers

    def _get_timeout_from_message(self, orig_message_raw, callback_id, headers):
        orig_message_raw = json.dumps(orig_message_raw)
        timeout_from_message = SmartAppFromMessage(orig_message_raw, headers=headers,
                                                   masking_fields=self.masking_fields)
        timeout_from_message.callback_id = callback_id
        return timeout_from_message

    def iterate_behavior_timeouts(self):
        now = time.time()
        while now > (self.behaviors_timeouts.get_head_key() or float("inf")):
            _, behavior_timeout_value = self.behaviors_timeouts.pop()
            db_uid, callback_id, mq_message, kafka_key = behavior_timeout_value
            try:
                save_tries = 0
                user_save_no_collisions = False
                user = None
                while save_tries < self.user_save_collisions_tries and not user_save_no_collisions:
                    save_tries += 1

                    orig_message_raw = json.loads(mq_message.value())
                    orig_message_raw[SmartAppFromMessage.MESSAGE_NAME] = message_names.LOCAL_TIMEOUT

                    timeout_from_message = self._get_timeout_from_message(orig_message_raw, callback_id,
                                                                          headers=mq_message.headers())

                    user = self.load_user(db_uid, timeout_from_message)
                    commands = self.model.answer(timeout_from_message, user)
                    topic_key = self._get_topic_key(mq_message)
                    answers = self._generate_answers(user=user, commands=commands, message=timeout_from_message,
                                                     topic_key=topic_key,
                                                     kafka_key=kafka_key)

                    user_save_no_collisions = self.save_user(db_uid, user, mq_message)

                    if user and not user_save_no_collisions:
                        log(
                            "MainLoop.iterate_behavior_timeouts: save user got collision on uid %(uid)s db_version %(db_version)s.",
                            user=user,
                            params={log_const.KEY_NAME: "ignite_collision",
                                    "db_uid": db_uid,
                                    "message_key": mq_message.key(),
                                    "kafka_key": kafka_key,
                                    "uid": user.id,
                                    "db_version": str(user.variables.get(user.USER_DB_VERSION))},
                            level="WARNING")

                        continue

                if not user_save_no_collisions:
                    log(
                        "MainLoop.iterate_behavior_timeouts: db_save collision all tries left on uid %(uid)s db_version %(db_version)s.",
                        user=user,
                        params={log_const.KEY_NAME: "ignite_collision",
                                "db_uid": db_uid,
                                "message_key": mq_message.key(),
                                "message_partition": mq_message.partition(),
                                "kafka_key": kafka_key,
                                "uid": user.id,
                                "db_version": str(user.variables.get(user.USER_DB_VERSION))},
                        level="WARNING")

                    smart_kit_metrics.counter_save_collision_tries_left(self.app_name)
                self.save_behavior_timeouts(user, mq_message, kafka_key)
                for answer in answers:
                    self._send_request(user, answer, mq_message)
            except:
                log("%(class_name)s error.", params={log_const.KEY_NAME: "error_handling_timeout",
                                                     "class_name": self.__class__.__name__,
                                                     log_const.REQUEST_VALUE: str(mq_message.value())},
                    level="ERROR", exc_info=True)

    def _get_topic_key(self, mq_message):
        return self.default_topic_key or self._topic_names[mq_message.topic()]

    def iterate(self, kafka_key):
        consumer = self.consumers[kafka_key]
        mq_message = None
        message_value = None
        try:
            mq_message = None
            message_value = None
            stats = ""
            with StatsTimer() as poll_timer:
                mq_message = consumer.poll()
            if mq_message:
                stats += "Polling time: {} msecs\n".format(poll_timer.msecs)
                topic_key = self._get_topic_key(mq_message)

                save_tries = 0
                user_save_no_collisions = False
                user = None
                db_uid = None
                while save_tries < self.user_save_collisions_tries and not user_save_no_collisions:
                    save_tries += 1
                    message_value = mq_message.value()
                    message = SmartAppFromMessage(message_value,
                                                  headers=mq_message.headers(),
                                                  masking_fields=self.masking_fields)

                    # TODO вернуть проверку ключа!!!
                    if message.validate():  # and self.check_message_key(message, mq_message.key()):
                        log("INCOMING FROM TOPIC: %(topic)s partition %(message_partition)s HEADERS: %(headers)s DATA: %(incoming_data)s",
                                      params={log_const.KEY_NAME: "incoming_message",
                                              "topic": mq_message.topic(),
                                              "message_partition": mq_message.partition(),
                                              "message_key": mq_message.key(),
                                              "kafka_key": kafka_key,
                                              "incoming_data": str(message.masked_value),
                                              "headers": str(mq_message.headers()),
                                              MESSAGE_ID_STR: message.incremental_id})

                        db_uid = message.db_uid

                        span = jaeger_utils.get_incoming_spam(self.tracer, message, mq_message)

                        with self.tracer.scope_manager.activate(span, True) as scope:
                            with StatsTimer() as load_timer:
                                user = self.load_user(db_uid, message)

                        with self.tracer.scope_manager.activate(span, True) as scope:
                            with self.tracer.start_span('Loading time', child_of=scope.span) as span:
                                smart_kit_metrics.sampling_load_time(self.app_name, load_timer.secs)
                                stats += "Loading time: {} msecs\n".format(load_timer.msecs)
                                with StatsTimer() as script_timer:
                                    commands = self.model.answer(message, user)

                            with self.tracer.start_span('Script time', child_of=scope.span) as span:
                                answers = self._generate_answers(user=user, commands=commands, message=message,
                                                                 topic_key=topic_key,
                                                                 kafka_key=kafka_key)
                                smart_kit_metrics.sampling_script_time(self.app_name, script_timer.secs)
                                stats += "Script time: {} msecs\n".format(script_timer.msecs)

                            with self.tracer.start_span('Saving time', child_of=scope.span) as span:
                                with StatsTimer() as save_timer:
                                    user_save_no_collisions = self.save_user(db_uid, user, message)

                            smart_kit_metrics.sampling_save_time(self.app_name, save_timer.secs)
                            stats += "Saving time: {} msecs\n".format(save_timer.msecs)
                            if not user_save_no_collisions:
                                log(
                                    "MainLoop.iterate: save user got collision on uid %(uid)s db_version %(db_version)s.",
                                    user=user,
                                    params={log_const.KEY_NAME: "ignite_collision",
                                            "db_uid": db_uid,
                                            "message_key": mq_message.key(),
                                            "message_partition": mq_message.partition(),
                                            "kafka_key": kafka_key,
                                            "uid": user.id,
                                            "db_version": str(user.variables.get(user.USER_DB_VERSION))},
                                    level="WARNING")
                                continue

                            self.save_behavior_timeouts(user, mq_message, kafka_key)

                        if mq_message.headers() is None:
                            mq_message.set_headers([])
                        self.tracer.inject(span_context=span.context, format=jaeger_kafka_codec.KAFKA_MAP,
                                           carrier=mq_message.headers())

                        if answers:
                            for answer in answers:
                                with StatsTimer() as publish_timer:
                                    self._send_request(user, answer, mq_message)
                                stats += "Publishing time: {} msecs".format(publish_timer.msecs)
                                log(stats)
                    else:
                        try:
                            data = message.masked_value
                        except:
                            data = "<DATA FORMAT ERROR>"
                        log(f"Message validation failed, skip message handling.",
                                      params={log_const.KEY_NAME: "invalid_message",
                                              "data": data}, level="ERROR")
                        smart_kit_metrics.counter_invalid_message(self.app_name)
                if user and not user_save_no_collisions:
                    log(
                        "MainLoop.iterate: db_save collision all tries left on uid %(uid)s db_version %(db_version)s.",
                        user=user,
                        params={log_const.KEY_NAME: "ignite_collision",
                                "db_uid": db_uid,
                                "message_key": mq_message.key(),
                                "message_partition": mq_message.partition(),
                                "kafka_key": kafka_key,
                                "uid": user.id,
                                "db_version": str(user.variables.get(user.USER_DB_VERSION))},
                        level="WARNING")

                    smart_kit_metrics.counter_save_collision_tries_left(self.app_name)
                consumer.commit_offset(mq_message)
        except KafkaException as kafka_exp:
            log("kafka error: %(kafka_exp)s. MESSAGE: {}.".format(message_value),
                params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                        "kafka_exp": str(kafka_exp),
                        log_const.REQUEST_VALUE: str(message_value)},
                level="ERROR", exc_info=True)
        except Exception:
            try:
                log("%(class_name)s iterate error. Kafka key %(kafka_key)s MESSAGE: {}.".format(message_value),
                    params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                            "kafka_key": kafka_key},
                    level="ERROR", exc_info=True)
                consumer.commit_offset(mq_message)
            except Exception:
                log("Error handling worker fail exception.",
                    level="ERROR", exc_info=True)


    def check_message_key(self, from_message, message_key):
        message_key = message_key or b""
        sub = from_message.sub
        channel = from_message.channel
        uid = from_message.uid
        if sub:
            valid_key = "{}_{}_{}".format(channel, sub, uid)
        else:
            valid_key = "{}_{}".format(channel, uid)
        key_str = message_key.decode()

        message_key_is_valid = key_str == valid_key
        if not message_key_is_valid:
            log("Failed to check Kafka message key %(message_key)s !=  %(valid_key)s",
                params={"message_key": key_str, "valid_key": valid_key},
                level="ERROR", exc_info=True)
        return message_key_is_valid

    def _send_request(self, user, answer, mq_message):
        kafka_broker_settings = self.settings["template_settings"].get(
            "route_kafka_broker"
        ) or []

        request = answer.request

        for kb_setting in kafka_broker_settings:
            if (
                kb_setting["from_channel"] == answer.incoming_message.channel
                and kb_setting["to_topic"] == request.topic_key
            ):
                request.kafka_key = kb_setting["route_to_broker"]

        request_params = dict()
        request_params["publishers"] = self.publishers
        request_params["mq_message"] = mq_message
        request_params["payload"] = answer.value
        request_params["masked_value"] = answer.masked_value
        request.run(answer.value, request_params)
        self._log_request(user, request, answer, mq_message)

    def _log_request(self, user, request, answer, original_mq_message):
        log("OUTGOING TO TOPIC_KEY: %(topic_key)s",
                      params={log_const.KEY_NAME: "outgoing_message",
                              "topic_key": request.topic_key,
                              "data": answer.masked_value}, user=user)

    @lazy
    def _topic_names(self):
        topics = self.settings["kafka"]["template-engine"]["main"]["consumer"]["topics"]
        return {name: key for key, name in topics.items()}

    @lazy
    def default_topic_key(self):
        return self.settings["kafka"]["template-engine"]["main"].get("default_topic_key")

    @lazy
    def masking_fields(self):
        return self.settings["template_settings"].get("masking_fields")

    def save_behavior_timeouts(self, user, mq_message, kafka_key):
        for i, (expire_time_us, callback_id) in enumerate(user.behaviors.get_behavior_timeouts()):
            # two behaviors can be created in one query, so we need add some salt to make theirs key unique
            unique_key = expire_time_us + i * 1e-5
            log(
                "%(class_name)s: adding local_timeout on callback %(callback_id)s with timeout on %(unique_key)s",
                params={log_const.KEY_NAME: "adding_local_timeout",
                        "class_name": self.__class__.__name__,
                        "callback_id": callback_id,
                        "unique_key": unique_key})
            self.behaviors_timeouts.push(unique_key, self.behaviors_timeouts_value_cls._make(
                (user.message.db_uid, callback_id, mq_message, kafka_key)))

        for callback_id in user.behaviors.get_returned_callbacks():
            log("%(class_name)s: removing local_timeout on callback %(callback_id)s",
                params={log_const.KEY_NAME: "removing_local_timeout",
                        "class_name": self.__class__.__name__,
                        "callback_id": callback_id})
            self.behaviors_timeouts.remove(callback_id)

    def stop(self, signum, frame):
        self.is_work = False
