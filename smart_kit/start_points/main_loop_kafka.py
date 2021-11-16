# coding=utf-8
import asyncio
import json
import time
import sys
from collections import namedtuple
from functools import lru_cache

from confluent_kafka.cimpl import KafkaException
from lazy import lazy

import scenarios.logging.logger_constants as log_const
from core.jaeger_custom_client import jaeger_utils
from core.jaeger_custom_client import kafka_codec as jaeger_kafka_codec
from core.logging.logger_utils import log, UID_STR, MESSAGE_ID_STR

from core.message.from_message import SmartAppFromMessage
from core.model.heapq.heapq_storage import HeapqKV
from core.mq.kafka.kafka_consumer import KafkaConsumer
from core.mq.kafka.kafka_publisher import KafkaPublisher
from core.utils.stats_timer import StatsTimer
from core.basic_models.actions.command import Command
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
    MAX_LOG_TIME = 20
    BAD_ANSWER_COMMAND = Command(message_names.ERROR, {"code": -1, "description": "Invalid Answer Message"})

    def __init__(self, *args, **kwargs):
        log("%(class_name)s.__init__ started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                        "class_name": self.__class__.__name__})
        self.health_check_server_future = None
        super().__init__(*args, **kwargs)

        try:
            kafka_config = _enrich_config_from_secret(
                self.settings["kafka"]["template-engine"], self.settings.get("secret_kafka", {})
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

            self.app_name = self.settings.app_name
            self.consumers = consumers
            for key in self.consumers:
                self.consumers[key].subscribe()
            self.publishers = publishers

            # is needed? start #
            self.behaviors_timeouts_value_cls = namedtuple('behaviors_timeouts_value',
                                                           'db_uid, callback_id, mq_message, kafka_key')
            self.behaviors_timeouts = HeapqKV(value_to_key_func=lambda val: val.callback_id)
            # is needed? end #

            self.concurrent_messages = 0

            log("%(class_name)s.__init__ completed.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__})
        except Exception:
            log("%(class_name)s.__init__ exception.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__},
                level="ERROR", exc_info=True)
            raise

    # TODO find where it should be used
    async def pre_handle(self):
        await self.iterate_behavior_timeouts()

    def run(self):
        log("%(class_name)s.run started", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                  "class_name": self.__class__.__name__})
        try:
            self.loop.run_until_complete(self.main_coro())
        except (SystemExit,):
            log("%(class_name)s.run stopped", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                      "class_name": self.__class__.__name__})

    async def main_coro(self):
        tasks = [self.main_work(kafka_key) for kafka_key in self.consumers]
        if self.health_check_server is not None:
            tasks.append(self.healthcheck_coro())
        await asyncio.gather(*tasks)

    async def healthcheck_coro(self):
        while self.is_work:
            if not self.health_check_server_future or self.health_check_server_future.done() or \
                    self.health_check_server_future.cancelled():
                self.health_check_server_future = self.loop.run_in_executor(None, self.health_check_server.iterate)
            await asyncio.sleep(0.5)

    async def main_work(self, kafka_key):
        consumer = self.consumers[kafka_key]
        message_value = None

        max_concurrent_messages = self.settings["template_settings"].get("max_concurrent_messages", 10)
        max_concurrent_messages_delay = self.settings["template_settings"].get("max_concurrent_messages_delay", 0.1)
        last_poll_begin_time = time.time()
        while self.is_work:
            from_last_poll_begin_ms = int((time.time() - last_poll_begin_time) * 1000)
            stats = "From last poll time: {} msecs\n".format(from_last_poll_begin_ms)
            log_params = {
                log_const.KEY_NAME: "timings",
                "from_last_poll_begin_ms": from_last_poll_begin_ms
            }
            last_poll_begin_time = time.time()
            if self.concurrent_messages >= max_concurrent_messages:
                log(f"main_loop.main_work: max {max_concurrent_messages} concurrent messages occured",
                    params={log_const.KEY_NAME: "max_concurrent_messages"}, level='WARNING')
                await asyncio.sleep(max_concurrent_messages_delay)
                total_delay = log_params.get("waiting_max_concurrent_messages", 0)
                total_delay += max_concurrent_messages_delay
                log_params["waiting_max_concurrent_messages"] = total_delay
                continue
            try:
                self.concurrent_messages += 1
                mq_message = None
                with StatsTimer() as poll_timer:
                    # Max delay between polls configured in consumer.poll_timeout param
                    mq_message = await self.loop.run_in_executor(None, consumer.poll)
                if mq_message:
                    headers = mq_message.headers()
                    if headers is None:
                        raise Exception("No incoming message headers found.")
                    stats += "Polling time: {} msecs\n".format(poll_timer.msecs)
                    log_params["kafka_polling"] = poll_timer.msecs
                    message_value = json.loads(mq_message.value())
                    await self.process_message(mq_message, consumer, kafka_key, stats, log_params)

            except KafkaException as kafka_exp:
                self.concurrent_messages -= 1
                log("kafka error: %(kafka_exp)s.",
                    params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                            "kafka_exp": str(kafka_exp),
                            log_const.REQUEST_VALUE: str(message_value)},
                    level="ERROR", exc_info=True)
            except Exception:
                self.concurrent_messages -= 1
                log("%(class_name)s iterate error. Kafka key %(kafka_key)s",
                    params={log_const.KEY_NAME: "worker_exception",
                            "kafka_key": kafka_key,
                            log_const.REQUEST_VALUE: str(message_value)},
                    level="ERROR", exc_info=True)
                try:
                    consumer.commit_offset(mq_message)
                except Exception:
                    log("Error handling worker fail exception.", level="ERROR", exc_info=True)
                    raise
            else:
                self.concurrent_messages -= 1

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
                                       masking_fields=self.masking_fields,
                                       validators=self.to_msg_validators)
            if answer.validate():
                answers.append(answer)
            else:
                answers.append(SmartAppToMessage(self.BAD_ANSWER_COMMAND, message=message, request=request))

            smart_kit_metrics.counter_outgoing(self.app_name, command.name, answer, user)

        return answers

    def _get_timeout_from_message(self, orig_message_raw, callback_id, headers):
        orig_message_raw = json.dumps(orig_message_raw)
        timeout_from_message = SmartAppFromMessage(orig_message_raw, headers=headers,
                                                   masking_fields=self.masking_fields,
                                                   validators=self.from_msg_validators)
        timeout_from_message.callback_id = callback_id
        return timeout_from_message

    async def iterate_behavior_timeouts(self):
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

                    user = await self.load_user(db_uid, timeout_from_message)
                    commands = await self.model.answer(timeout_from_message, user)
                    topic_key = self._get_topic_key(mq_message, kafka_key)
                    answers = self._generate_answers(user=user, commands=commands, message=timeout_from_message,
                                                     topic_key=topic_key,
                                                     kafka_key=kafka_key)

                    user_save_no_collisions = await self.save_user(db_uid, user, mq_message)

                    if user and not user_save_no_collisions:
                        log("MainLoop.iterate_behavior_timeouts: save user got collision on uid %(uid)s db_version %(db_version)s.",
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
                    log("MainLoop.iterate_behavior_timeouts: db_save collision all tries left on uid %(uid)s db_version %(db_version)s.",
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

    def _get_topic_key(self, mq_message, kafka_key):
        topic_names_2_key = self._topic_names_2_key(kafka_key)
        return self.default_topic_key(kafka_key) or topic_names_2_key[mq_message.topic()]

    async def process_message(self, mq_message, consumer, kafka_key, stats, log_params):
        topic_key = self._get_topic_key(mq_message, kafka_key)
        save_tries = 0
        user_save_ok = False
        user = None
        db_uid = None
        validation_failed = False
        while save_tries < self.user_save_collisions_tries and not user_save_ok:
            save_tries += 1
            message_value = mq_message.value()
            message = SmartAppFromMessage(message_value,
                                          headers=mq_message.headers(),
                                          masking_fields=self.masking_fields,
                                          creation_time=consumer.get_msg_create_time(mq_message))

            # TODO вернуть проверку ключа!!!
            if message.validate():
                waiting_message_time = 0
                if message.creation_time:
                    waiting_message_time = time.time() * 1000 - message.creation_time
                    stats += "Waiting message: {} msecs\n".format(waiting_message_time)
                    log_params["waiting_message"] = waiting_message_time

                stats += "Mid: {}\n".format(message.incremental_id)
                log_params[MESSAGE_ID_STR] = message.incremental_id
                smart_kit_metrics.sampling_mq_waiting_time(self.app_name, waiting_message_time / 1000)

                if self._is_message_timeout_to_skip(message, waiting_message_time):
                    skip_timeout = True
                    break

                self.check_message_key(message, mq_message.key(), user)
                log("INCOMING FROM TOPIC: %(topic)s partition %(message_partition)s HEADERS: %(headers)s DATA: %(incoming_data)s",
                    params={log_const.KEY_NAME: "incoming_message",
                            "topic": mq_message.topic(),
                            "message_partition": mq_message.partition(),
                            "message_key": mq_message.key(),
                            "kafka_key": kafka_key,
                            "incoming_data": str(message.masked_value),
                            "headers": str(mq_message.headers()),
                            "waiting_message": waiting_message_time,
                            "surface": message.device.surface,
                            MESSAGE_ID_STR: message.incremental_id},
                    user=user
                    )

                db_uid = message.db_uid

                span = jaeger_utils.get_incoming_spam(self.tracer, message, mq_message)

                with self.tracer.scope_manager.activate(span, True) as scope:
                    with self.tracer.start_span('Loading time', child_of=scope.span) as span:
                        with StatsTimer() as load_timer:
                            user = await self.load_user(db_uid, message)

                    with self.tracer.start_span('Loading time', child_of=scope.span) as span:
                        smart_kit_metrics.sampling_load_time(self.app_name, load_timer.secs)
                        stats += "Loading time: {} msecs\n".format(load_timer.msecs)
                        with StatsTimer() as script_timer:
                            commands = await self.model.answer(message, user)

                    with self.tracer.start_span('Script time', child_of=scope.span) as span:
                        answers = self._generate_answers(user=user, commands=commands, message=message,
                                                         topic_key=topic_key,
                                                         kafka_key=kafka_key)
                        stats += "Script time: {} msecs\n".format(script_timer.msecs)
                        log_params["script_time"] = script_timer.msecs
                        smart_kit_metrics.sampling_script_time(self.app_name, script_timer.secs)

                    with self.tracer.start_span('Saving time', child_of=scope.span) as span:
                        with StatsTimer() as save_timer:
                            user_save_ok = await self.save_user(db_uid, user, message)

                    stats += "Saving user to DB time: {} msecs\n".format(save_timer.msecs)
                    log_params["user_saving"] = save_timer.msecs
                    smart_kit_metrics.sampling_save_time(self.app_name, save_timer.secs)
                    if not user_save_ok:
                        log("MainLoop.iterate: save user got collision on uid %(uid)s db_version %(db_version)s.",
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

                    if answers:
                        self.save_behavior_timeouts(user, mq_message, kafka_key)

                if mq_message.headers() is None:
                    mq_message.set_headers([])
                self.tracer.inject(span_context=span.context, format=jaeger_kafka_codec.KAFKA_MAP,
                                   carrier=mq_message.headers())

                if answers:
                    for answer in answers:
                        with StatsTimer() as publish_timer:
                            self._send_request(user, answer, mq_message)
                            smart_kit_metrics.counter_outgoing(self.app_name, answer.command.name, answer, user)
                        stats += "Publishing time: {} msecs".format(publish_timer.msecs)
                        log_params["kafka_publishing"] = publish_timer.msecs
                        log(stats)
            else:
                validation_failed = True
                try:
                    data = message.masked_value
                except:
                    data = "<DATA FORMAT ERROR>"
                log(f"Message validation failed, skip message handling.",
                    params={log_const.KEY_NAME: "invalid_message",
                            "data": data}, level="ERROR")
                smart_kit_metrics.counter_invalid_message(self.app_name)
                break
        if stats:
            log(stats, user=user, params=log_params)

        if user and not user_save_ok and not validation_failed:
            log("MainLoop.iterate: db_save collision all tries left on uid %(uid)s db_version %(db_version)s.",
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

    def _is_message_timeout_to_skip(self, message, waiting_message_time):
        # Returns True if timeout is found
        waiting_message_timeout = self.settings["template_settings"].get("waiting_message_timeout", {})
        warning_delay = waiting_message_timeout.get('warning', 200)
        skip_delay = waiting_message_timeout.get('skip', 8000)
        log_level = None
        make_break = False

        if waiting_message_time >= skip_delay:
            # Too old message
            log_level = "ERROR"
            make_break = True

        elif waiting_message_time >= warning_delay:
            # Warn, but continue message processing
            log_level = "WARNING"
            smart_kit_metrics.counter_mq_long_waiting(self.app_name)

        if log_level is not None:
            log(
                f"Out of time message %(waiting_message_time)s msecs, "
                f"mid: %(mid)s {message.as_dict}",
                params={
                    log_const.KEY_NAME: "waiting_message_timeout",
                    "waiting_message_time": waiting_message_time,
                    "mid": message.incremental_id
                },
                level=log_level)
        return make_break

    def check_message_key(self, from_message, message_key, user):
        sub = from_message.sub
        channel = from_message.channel
        uid = from_message.uid
        message_key = message_key or b""
        try:
            params = [channel, sub, uid]
            valid_key = ""
            for value in params:
                if value:
                    valid_key = "{}{}{}".format(valid_key, "_", value) if valid_key else "{}".format(value)
            key_str = message_key.decode()

            message_key_is_valid = key_str == valid_key
            if not message_key_is_valid:
                log(f"Failed to check Kafka message key {message_key} !=  {valid_key}",
                    params={
                        log_const.KEY_NAME: "check_kafka_key_validation",
                        MESSAGE_ID_STR: from_message.incremental_id,
                        UID_STR: uid
                    }, user=user,
                    level="WARNING")
        except:
            log(f"Exception to check Kafka message key {message_key}",
                params={log_const.KEY_NAME: "check_kafka_key_error",
                        MESSAGE_ID_STR: from_message.incremental_id,
                        UID_STR: uid
                        }, user=user, level="ERROR")

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
                    "headers": str(request._get_new_headers(original_mq_message)),
                    "data": answer.masked_value}, user=user)

    @lru_cache()
    def _topic_names_2_key(self, kafka_key):
        topics = self.settings["kafka"]["template-engine"][kafka_key]["consumer"]["topics"]
        return {name: key for key, name in topics.items()}

    def default_topic_key(self, kafka_key):
        return self.settings["kafka"]["template-engine"][kafka_key].get("default_topic_key")

    @lazy
    def masking_fields(self):
        return self.settings["template_settings"].get("masking_fields")

    def save_behavior_timeouts(self, user, mq_message, kafka_key):
        for i, (timeout, callback_id) in enumerate(user.behaviors.get_behavior_timeouts()):
            # если колбеков много, разносим их на 1 секунду друг от друга во избежание коллизий
            timeout = timeout + i
            log("%(class_name)s: adding local_timeout on callback %(callback_id)s with timeout in %(timeout)s seconds.",
                params={log_const.KEY_NAME: "adding_local_timeout",
                        "class_name": self.__class__.__name__,
                        "callback_id": callback_id,
                        "timeout": timeout})

            self.loop.call_later(
                timeout,
                self.loop.create_task,
                self.do_behavior_timeout(user.message.db_uid, callback_id, mq_message, kafka_key)
            )

    def stop(self, signum, frame):
        log("Stop call!")
        log("Stopping Kafka handler", level="WARNING")
        for kafka_key in self.consumers:
            self.consumers[kafka_key].close()
            log("Kafka consumer connection is closed", level="WARNING")
            self.publishers[kafka_key].close()
            log("Kafka publisher connection is closed", level="WARNING")
        log("Kafka handler is stopped", level="WARNING")
        self.is_work = False

    async def do_behavior_timeout(self, db_uid, callback_id, mq_message, kafka_key):
        if not self.is_work:
            return
        try:
            save_tries = 0
            user_save_ok = False
            answers = []
            user = None
            while save_tries < self.user_save_collisions_tries and not user_save_ok:
                callback_found = False
                log(f"MainLoop.do_behavior_timeout: handling callback {callback_id}. for db_uid {db_uid}. try {save_tries}.")

                save_tries += 1

                orig_message_raw = json.loads(mq_message.value())
                orig_message_raw[SmartAppFromMessage.MESSAGE_NAME] = message_names.LOCAL_TIMEOUT

                timeout_from_message = self._get_timeout_from_message(orig_message_raw, callback_id,
                                                                      headers=mq_message.headers())

                user = await self.load_user(db_uid, timeout_from_message)
                # TODO:  not to load user to check behaviors.has_callback ?
                if user.behaviors.has_callback(callback_id):
                    callback_found = True
                    commands = await self.model.answer(timeout_from_message, user)
                    topic_key = self._get_topic_key(mq_message, kafka_key)
                    answers = self._generate_answers(user=user, commands=commands, message=timeout_from_message,
                                                     topic_key=topic_key,
                                                     kafka_key=kafka_key)

                    user_save_ok = await self.save_user(db_uid, user, mq_message)

                    if not user_save_ok:
                        log("MainLoop.iterate_behavior_timeouts: save user got collision on uid %(uid)s db_version %(db_version)s.",
                            user=user,
                            params={log_const.KEY_NAME: "ignite_collision",
                                    "db_uid": db_uid,
                                    "message_key": mq_message.key(),
                                    "kafka_key": kafka_key,
                                    "uid": user.id,
                                    "db_version": str(user.variables.get(user.USER_DB_VERSION))},
                            level="WARNING")

            if not user_save_ok and callback_found:
                log("MainLoop.iterate_behavior_timeouts: db_save collision all tries left on uid %(uid)s db_version %(db_version)s.",
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
            if user_save_ok:
                self.save_behavior_timeouts(user, mq_message, kafka_key)
                for answer in answers:
                    self._send_request(user, answer, mq_message)
        except:
            log("%(class_name)s error.", params={log_const.KEY_NAME: "error_handling_timeout",
                                                 "class_name": self.__class__.__name__,
                                                 log_const.REQUEST_VALUE: str(mq_message.value())},
                level="ERROR", exc_info=True)
