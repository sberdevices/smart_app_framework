# coding=utf-8
import asyncio
import cProfile
import gc
import hashlib
import json
import pstats
import random
import signal
import concurrent.futures
import tracemalloc
from functools import lru_cache

from confluent_kafka.cimpl import KafkaException
from lazy import lazy

import scenarios.logging.logger_constants as log_const
from core.logging.logger_utils import log, UID_STR, MESSAGE_ID_STR

from core.message.from_message import SmartAppFromMessage
from core.mq.kafka.async_kafka_publisher import AsyncKafkaPublisher
from core.mq.kafka.kafka_consumer import KafkaConsumer
from core.utils.memstats import get_top_malloc
from core.utils.stats_timer import StatsTimer
from core.basic_models.actions.command import Command
from core.utils.utils import current_time_ms
from smart_kit.compatibility.commands import combine_commands
from smart_kit.message.get_to_message import get_to_message
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
    # in milliseconds. log event if elapsed time more than value
    MAX_LOG_TIME = 20
    BAD_ANSWER_COMMAND = Command(message_names.ERROR, {"code": -1, "description": "Invalid Answer Message"})

    def __init__(self, *args, **kwargs):
        log("%(class_name)s.__init__ started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                        "class_name": self.__class__.__name__})
        self.loop = asyncio.get_event_loop()
        # We have many async loops for messages processing in main thread
        # And 1 thread for independent consecutive Kafka reading
        self.health_check_server_future = None
        super().__init__(*args, **kwargs)
        # We have many async loops for messages processing in main thread
        # And 1 thread for independent consecutive Kafka reading
        self.kafka_executor_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self._timers = dict()  # stores aio timers for callbacks
        self.template_settings = self.settings["template_settings"]
        self.worker_tasks = []

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
                    publishers.update({key: AsyncKafkaPublisher(kafka_config[key])})
            log(
                "%(class_name)s FINISHED CONSUMERS/PUBLISHERS CREATE",
                params={"class_name": self.__class__.__name__}, level="WARNING"
            )

            self.app_name = self.settings.app_name
            self.consumers = consumers
            for key in self.consumers:
                self.consumers[key].subscribe()
            self.publishers = publishers
            self.concurrent_messages = 0

            log("%(class_name)s.__init__ completed.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__})
        except Exception:
            log("%(class_name)s.__init__ exception.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__},
                level="ERROR", exc_info=True)
            raise

    def run(self):
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        log("%(class_name)s.run started", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                  "class_name": self.__class__.__name__})
        # try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.general_coro())

        log("MainLoop stopping kafka", level="WARNING")

        for kafka_key in self.consumers:
            self.consumers[kafka_key].close()
        for kafka_key in self.publishers:
            self.publishers[kafka_key].close()
        # except (SystemExit,) as e:
        log("MainLoop EXIT.", level="WARNING")
        # raise e

    async def general_coro(self):
        tasks = [self.process_consumer(kafka_key) for kafka_key in self.consumers]
        if self.health_check_server is not None:
            tasks.append(self.healthcheck_coro())
        await asyncio.gather(*tasks)

    async def healthcheck_coro(self):
        while self.is_work:
            if not self.health_check_server_future or self.health_check_server_future.done() or \
                    self.health_check_server_future.cancelled():
                self.health_check_server_future = self.loop.run_in_executor(None, self.health_check_server.iterate)
            await asyncio.sleep(0.5)
        log("healthcheck_coro stopped")

    async def process_consumer(self, kafka_key):
        consumer = self.consumers[kafka_key]
        loop = asyncio.get_event_loop()
        max_concurrent_messages = self.template_settings.get("max_concurrent_messages", 100)
        total_messages = 0

        profiling_settings = self.template_settings.get("profiling", {})
        profile_cpu = profiling_settings.get("cpu", False)
        profile_cpu_path = profiling_settings.get("cpu_path", "/tmp/dp.cpu.prof")
        profile_memory = profiling_settings.get("memory", False)
        profile_memory_log_delta = profiling_settings.get("memory_log_delta", 30)
        profile_memory_depth = profiling_settings.get("memory_depth", 4)

        async def worker(iteration, queue):
            nonlocal total_messages
            message_value = None
            user = None
            validation_failed = False
            last_poll_begin_time = self.loop.time()
            last_mem_log = self.loop.time()
            log(f"-- Starting {iteration} iter")

            while self.is_work:
                if profile_memory and iteration == 0 and self.loop.time() - last_mem_log > profile_memory_log_delta:
                    top = get_top_malloc(trace_limit=0)
                    async_counts = len(self.loop._ready), len(self.loop._scheduled), len(self.loop._asyncgens)
                    async_values = " + ".join(map(str, async_counts))
                    log(
                        f"Total memory: {top}; "
                        f"Async: {async_values} = {sum(async_counts)}; "
                        f"Trash: {gc.get_count()} ",
                        level="DEBUG"
                    )
                    last_mem_log = self.loop.time()

                from_last_poll_begin_ms = int((self.loop.time() - last_poll_begin_time) * 1000)
                stats = f"From last message coro {iteration} time: {from_last_poll_begin_ms} msecs\n"
                log_params = {
                    log_const.KEY_NAME: "timings",
                    "from_last_poll_begin_ms": from_last_poll_begin_ms,
                    "iteration": iteration
                }
                last_poll_begin_time = self.loop.time()

                try:
                    mq_message = await queue.get()
                    self.concurrent_messages += 1
                    if mq_message:
                        log(f"\n-- Processing {self.concurrent_messages} msgs at {iteration} iter\n")
                        total_messages += 1
                        headers = mq_message.headers()
                        if headers is None:
                            raise Exception("No incoming message headers found.")
                        message_value = json.loads(mq_message.value())
                        await self.process_message(mq_message, consumer, kafka_key, stats, log_params)

                except KafkaException as kafka_exp:
                    self.concurrent_messages -= 1
                    log("kafka error: %(kafka_exp)s.",
                        params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                "kafka_exp": str(kafka_exp),
                                log_const.REQUEST_VALUE: str(message_value)},
                        level="ERROR", exc_info=True)
                    queue.task_done()

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
                    queue.task_done()
                else:
                    self.concurrent_messages -= 1
                    queue.task_done()

            # END while self.is_work
            log(f"-- Stop {iteration} iter")

        start_time = self.loop.time()
        if profile_cpu:
            cpu_pr = cProfile.Profile()
            cpu_pr.enable()
        else:
            cpu_pr = None
        if profile_memory:
            tracemalloc.start(profile_memory_depth)

        log(f"Starting %(class_name)s in {max_concurrent_messages} coro",
            params={"class_name": self.__class__.__name__})

        # TODO: think about queue maxsize
        queues = [asyncio.Queue() for _ in range(max_concurrent_messages)]

        for i, queue in enumerate(queues):
            task = asyncio.create_task(worker(f'worker-{i}', queue))
            self.worker_tasks.append(task)

        await self.poll_kafka(consumer, queues)  # blocks while self.is_works

        log("waiting for process unfinished tasks in queues")
        await asyncio.gather(*(queue.join() for queue in queues))

        time_delta = self.loop.time() - start_time
        log(f"Process Consumer exit: {total_messages} msg in {int(time_delta)} sec", level="DEBUG")

        t = self.loop.time()
        delay = self.template_settings.get("behavior_timers_tear_down_delay", 15)
        log(f"wait timers to do their jobs for {delay} secs...")
        while self._timers and (self.loop.time() - t) < delay:
            await asyncio.sleep(1)

        for task in self.worker_tasks:
            cancell_status = task.cancel()
            log(f"{task} cancell status: {cancell_status} ")

        log(f"Stop consuming messages. All workers closed, erasing {len(self._timers)} timers.")

        if profile_memory:
            log(f"{get_top_malloc(trace_limit=16)}")
            tracemalloc.stop()
        if cpu_pr is not None:
            cpu_pr.disable()
            stats = pstats.Stats(cpu_pr)
            stats.sort_stats(pstats.SortKey.TIME)
            stats.print_stats(10)
            stats.dump_stats(filename=profile_cpu_path)

    async def poll_kafka(self, consumer, queues):
        while self.is_work:
            with StatsTimer() as poll_timer:
                # Max delay between polls configured in consumer.poll_timeout param
                mq_message = consumer.poll()
            if poll_timer.msecs > self.MAX_LOG_TIME:
                log_params = {"kafka_polling": poll_timer.msecs}
                log(f"Long poll time: %(kafka_polling)s msecs\n", params=log_params, level="WARNING")

            if mq_message:
                key = mq_message.key()
                if key:
                    queue_index = int(hashlib.sha1(key).hexdigest(), 16) % len(queues)
                else:
                    queue_index = random.randrange(len(queues))

                # this will block if queue is full!
                await queues[queue_index].put(mq_message)
            else:
                await asyncio.sleep(self.template_settings.get("no_kafka_messages_poll_time", 0.01))
        log(f"Stop poll_kafka consumer.")

    def _generate_answers(self, user, commands, message, **kwargs):
        topic_key = kwargs["topic_key"]
        kafka_key = kwargs["kafka_key"]
        answers = []
        commands = commands or []

        commands = combine_commands(commands, user)

        for command in commands:
            request = SmartKitKafkaRequest(id=None, items=command.request_data)
            request.update_empty_items({"topic_key": topic_key, "kafka_key": kafka_key})
            to_message = get_to_message(command.name)
            answer = to_message(command=command, message=message, request=request,
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

    def _get_topic_key(self, mq_message, kafka_key):
        topic_names_2_key = self._topic_names_2_key(kafka_key)
        return self.default_topic_key(kafka_key) or topic_names_2_key[mq_message.topic()]

    async def process_message(self, mq_message, consumer, kafka_key, stats, log_params):
        user = None
        topic_key = self._get_topic_key(mq_message, kafka_key)
        save_tries = 0
        user_save_ok = False
        skip_timeout = False
        db_uid = None
        validation_failed = False
        message_handled_ok = False
        while save_tries < self.user_save_collisions_tries and not user_save_ok:
            save_tries += 1
            message_value = mq_message.value()
            message = SmartAppFromMessage(message_value, headers=mq_message.headers(),
                                          masking_fields=self.masking_fields,
                                          creation_time=consumer.get_msg_create_time(mq_message))

            if message.validate():
                log(
                    "Incoming RAW message: %(message)s", params={"message": message.masked_value},
                    level="DEBUG")
                waiting_message_time = 0
                if message.creation_time:
                    waiting_message_time = current_time_ms() - message.creation_time
                    stats += f"Waiting message: {waiting_message_time} msecs\n"
                    log_params["waiting_message"] = waiting_message_time

                stats += f"Mid: {message.incremental_id}\n"
                log_params[MESSAGE_ID_STR] = message.incremental_id

                smart_kit_metrics.sampling_mq_waiting_time(self.app_name, waiting_message_time / 1000)

                if self._is_message_timeout_to_skip(message, waiting_message_time):
                    skip_timeout = True
                    break

                db_uid = message.db_uid
                with StatsTimer() as load_timer:
                    user = await self.load_user(db_uid, message)
                self.check_message_key(message, mq_message.key(), user)
                stats += f"Loading user time from DB time: {load_timer.msecs} msecs\n"
                log_params["user_loading"] = load_timer.msecs
                smart_kit_metrics.sampling_load_time(self.app_name, load_timer.secs)

                log(
                    "INCOMING FROM TOPIC: %(topic)s partition %(message_partition)s HEADERS: %(headers)s DATA: %("
                    "incoming_data)s",
                    params={log_const.KEY_NAME: "incoming_message",
                            "topic": mq_message.topic(),
                            "message_partition": mq_message.partition(),
                            "message_key": mq_message.key(),
                            "kafka_key": kafka_key,
                            "incoming_data": str(message.masked_value),
                            "length": len(message.value),
                            "headers": str(mq_message.headers()),
                            "waiting_message": waiting_message_time,
                            "surface": message.device.surface,
                            MESSAGE_ID_STR: message.incremental_id},
                    user=user
                    )

                with StatsTimer() as script_timer:
                    commands = await self.model.answer(message, user)

                answers = self._generate_answers(user=user, commands=commands, message=message, topic_key=topic_key,
                                                 kafka_key=kafka_key)

                stats += f"Script time: {script_timer.msecs} msecs\n"
                log_params["script_time"] = script_timer.msecs
                smart_kit_metrics.sampling_script_time(self.app_name, script_timer.secs)

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
                                "message_key": (mq_message.key() or b"").decode('utf-8', 'backslashreplace'),
                                "message_partition": mq_message.partition(),
                                "kafka_key": kafka_key,
                                "uid": user.id,
                                "db_version": str(user.variables.get(user.USER_DB_VERSION))},
                        level="WARNING")
                    continue

                message_handled_ok = True
                if answers:
                    self.save_behavior_timeouts(user, mq_message, kafka_key)

                if answers:
                    for answer in answers:
                        with StatsTimer() as publish_timer:
                            self._send_request(user, answer, mq_message)
                            smart_kit_metrics.counter_outgoing(self.app_name, answer.command.name, answer, user)
                        stats += "Publishing to Kafka time: {publish_timer.msecs} msecs\n"
                        log_params["kafka_publishing"] = publish_timer.msecs
            else:
                validation_failed = True
                data = None
                mid = None
                try:
                    data = message.masked_value
                    mid = message.incremental_id
                except:
                    pass
                log(f"Message validation failed, skip message handling.",
                    params={log_const.KEY_NAME: "invalid_message",
                            "data": data,
                            MESSAGE_ID_STR: mid}, level="ERROR")
                smart_kit_metrics.counter_invalid_message(self.app_name)
                break
        if stats:
            log(stats, user=user, params=log_params)

        if user and not user_save_ok and not validation_failed and not skip_timeout:
            log("MainLoop.iterate: db_save collision all tries left on uid %(uid)s db_version %(db_version)s.",
                user=user,
                params={log_const.KEY_NAME: "ignite_collision",
                        "db_uid": db_uid,
                        "message_key": (mq_message.key() or b"").decode('utf-8', 'backslashreplace'),
                        "message_partition": mq_message.partition(),
                        "kafka_key": kafka_key,
                        "uid": user.id,
                        "db_version": str(user.variables.get(user.USER_DB_VERSION))},
                level="WARNING")
            smart_kit_metrics.counter_save_collision_tries_left(self.app_name)

        consumer.commit_offset(mq_message)
        if message_handled_ok:
            self.remove_timer(message)

    def remove_timer(self, kafka_message):
        if kafka_message.has_callback_id:
            timer = self._timers.pop(kafka_message.callback_id, None)
            if timer is not None:
                log(f"Removing aio timer for callback {kafka_message.callback_id}. Have {len(self._timers)} running "
                    f"timers.", level="DEBUG")
                timer.cancel()

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
        valid_key = "_".join([i for i in [channel, sub, uid] if i])

        try:
            message_key = message_key or b""
            if isinstance(message_key, bytes):
                message_key = message_key.decode()
        except UnicodeDecodeError:
            log(f"Decode error to check Kafka message key {message_key}",
                params={log_const.KEY_NAME: "check_kafka_key_error",
                        MESSAGE_ID_STR: from_message.incremental_id,
                        UID_STR: uid
                        }, user=user, level="ERROR")

        if message_key != valid_key:
            log(f"Failed to check Kafka message key {message_key} != {valid_key}",
                params={
                    log_const.KEY_NAME: "check_kafka_key_validation",
                    MESSAGE_ID_STR: from_message.incremental_id,
                    UID_STR: uid
                }, user=user,
                level="WARNING")

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
        log("OUTGOING TO TOPIC_KEY: %(topic_key)s DATA: %(data)s",
            params={log_const.KEY_NAME: "outgoing_message",
                    "topic_key": request.topic_key,
                    "headers": str(request._get_new_headers(original_mq_message)),
                    "data": answer.masked_value,
                    "length": len(answer.value)}, user=user)

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
        for (behavior_delay, callback_id) in user.behaviors.get_behavior_timeouts():
            log("%(class_name)s: adding local_timeout on callback %(callback_id)s with delay in %(delay)s seconds.",
                params={log_const.KEY_NAME: "adding_local_timeout",
                        "class_name": self.__class__.__name__,
                        "callback_id": callback_id,
                        "delay": behavior_delay})

            self._timers[callback_id] = self.loop.call_later(
                behavior_delay, self.loop.create_task,
                self.do_behavior_timeout(user.message.db_uid, callback_id, mq_message, kafka_key)
            )

    def stop(self, signum, frame):
        log("Stop signal handler!")
        self.is_work = False

    async def do_behavior_timeout(self, db_uid, callback_id, mq_message, kafka_key):
        try:
            save_tries = 0
            user_save_ok = False
            answers = []
            user = None
            while save_tries < self.user_save_collisions_tries and not user_save_ok:
                callback_found = False
                log(f"MainLoop.do_behavior_timeout: handling callback {callback_id}. for db_uid {db_uid}. try "
                    f"{save_tries}.")

                save_tries += 1

                orig_message_raw = json.loads(mq_message.value())
                orig_message_raw[SmartAppFromMessage.MESSAGE_NAME] = message_names.LOCAL_TIMEOUT

                timeout_from_message = self._get_timeout_from_message(orig_message_raw, callback_id,
                                                                      headers=mq_message.headers())

                user = await self.load_user(db_uid, timeout_from_message)
                # TODO:  not to load user to check behaviors.has_callback ?

                self.remove_timer(timeout_from_message)

                if user.behaviors.has_callback(callback_id):
                    callback_found = True
                    commands = await self.model.answer(timeout_from_message, user)
                    topic_key = self._get_topic_key(mq_message, kafka_key)
                    answers = self._generate_answers(user=user, commands=commands, message=timeout_from_message,
                                                     topic_key=topic_key,
                                                     kafka_key=kafka_key)

                    user_save_ok = await self.save_user(db_uid, user, mq_message)

                    if not user_save_ok:
                        log("MainLoop.do_behavior_timeout: save user got collision on uid %(uid)s db_version %("
                            "db_version)s.",
                            user=user,
                            params={log_const.KEY_NAME: "ignite_collision",
                                    "db_uid": db_uid,
                                    "message_key": mq_message.key(),
                                    "kafka_key": kafka_key,
                                    "uid": user.id,
                                    "db_version": str(user.variables.get(user.USER_DB_VERSION))},
                            level="WARNING")

            if not user_save_ok and callback_found:
                log("MainLoop.do_behavior_timeout: db_save collision all tries left on uid %(uid)s db_version "
                    "%(db_version)s.",
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

    def _incoming_message_log(self, user, mq_message, message, kafka_key, waiting_message_time):
        log(
            "INCOMING FROM TOPIC: %(topic)s partition %(message_partition)s HEADERS: %(headers)s DATA: %("
            "incoming_data)s",
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
