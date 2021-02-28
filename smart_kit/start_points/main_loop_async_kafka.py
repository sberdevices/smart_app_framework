# coding=utf-8
import asyncio
import json
import time
from collections import namedtuple
from copy import deepcopy
from confluent_kafka.cimpl import KafkaException

import scenarios.logging.logger_constants as log_const
from core.jaeger_custom_client import jaeger_utils
from core.jaeger_custom_client import kafka_codec as jaeger_kafka_codec
from core.logging.logger_utils import log
from core.message.from_message import SmartAppFromMessage
from core.model.heapq.heapq_storage import HeapqKV
from core.utils.stats_timer import StatsTimer
from smart_kit.names import message_names
from smart_kit.start_points.main_loop_kafka import MainLoop
from smart_kit.utils.monitoring import smart_kit_metrics
from core.mq.kafka.aio_kafka_consumer import KafkaConsumer
from core.mq.kafka.aio_kafka_publisher import KafkaPublisher


def _enrich_config_from_secret(kafka_config, secret_config):
    for key in kafka_config:
        if secret_config.get(key):
            kafka_config[key]["consumer"]["conf"].update(secret_config[key]["consumer"]["conf"])
            kafka_config[key]["publisher"]["conf"].update(secret_config[key]["publisher"]["conf"])
    return kafka_config


class AIOKafkaMainLoop(MainLoop):

    def __init__(self, model, user_cls, parametrizer_cls, settings, *args, **kwargs):
        super().__init__(model, user_cls, parametrizer_cls, settings, create_kafka=False, *args, **kwargs)
        log("%(class_name)s.__init__ started.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                        "class_name": self.__class__.__name__})
        try:
            self.kafka_config = _enrich_config_from_secret(settings["kafka"]["template-engine"],
                                                           settings.get("secret_kafka", {}))
            self.consumers = []
            self.publishers = []
            log(
                "%(class_name)s START CONSUMERS/PUBLISHERS CREATE",
                params={"class_name": self.__class__.__name__}, level="WARNING"
            )
            log(
                "%(class_name)s FINISHED CONSUMERS/PUBLISHERS CREATE",
                params={"class_name": self.__class__.__name__}, level="WARNING"
            )

            self.settings = settings
            self.app_name = self.settings.app_name
            self.model = model
            self.user_cls = user_cls
            self.parametrizer_cls = parametrizer_cls
            self.behaviors_timeouts_value_cls = namedtuple('behaviors_timeouts_value',
                                                           'db_uid, callback_id, mq_message, kafka_key')
            self.behaviors_timeouts = HeapqKV(value_to_key_func=lambda val: val.callback_id)
            self.tracer.codecs["kafka_map"].is_async = True
            log("%(class_name)s.__init__ completed.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__})
        except:
            log("%(class_name)s.__init__ exception.", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                              "class_name": self.__class__.__name__},
                level="ERROR", exc_info=True)
            raise

    def run(self):
        for key, config in self.kafka_config.items():
            if config.get("consumer"):
                self.consumers.append(key)
            if config.get("publisher"):
                self.publishers.append(key)
        log("%(class_name)s.run started", params={log_const.KEY_NAME: log_const.STARTUP_VALUE,
                                                  "class_name": self.__class__.__name__})
        loop = asyncio.get_event_loop()#.run_until_complete(self._run())
        for kafka_key in self.consumers:
            loop.create_task(self.iterate(kafka_key, loop))
        #loop.create_task(self.health_check_server.iterate())
        # loop.create_task(self._run())
        loop.run_forever()

        log("Stopping Kafka handler", level="WARNING")

    def _get_topic_key(self, mq_message):
        return self.default_topic_key or self._topic_names[mq_message.topic]

    async def iterate(self, kafka_key, loop):
        consumer = KafkaConsumer(self.kafka_config[kafka_key])
        producer = KafkaPublisher(self.kafka_config[kafka_key])
        # Get cluster layout and join group `my-group`
        await consumer.start()
        await producer.start()
        try:
            # Consume messages
            async for msg in consumer:
                loop.create_task(self._iterate(msg, kafka_key, producer))
                # Get cluster layout and initial topic/partition leadership information
                # Produce message
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await consumer.stop()
            await producer.stop()

    async def _iterate(self, mq_message, kafka_key, producer):
        answers = self.__iterate(mq_message, kafka_key)
        if answers:
            for answer in answers:
                await producer.send_and_wait(self._get_topic_key(mq_message), bytearray(answer.value, 'utf-8'))
        self.health_check_server.iterate()

    def __iterate(self, mq_message, kafka_key):
        message_value = None
        try:
            topic_key = self._get_topic_key(mq_message)

            save_tries = 0
            user_save_no_collisions = False
            user = None
            db_uid = None
            while save_tries < self.user_save_collisions_tries and not user_save_no_collisions:
                save_tries += 1
                message_value = mq_message.value
                message = SmartAppFromMessage(message_value,
                                              headers=mq_message.headers,
                                              masking_fields=self.masking_fields)

                # TODO вернуть проверку ключа!!!
                if message.validate():  # and self.check_message_key(message, mq_message.key()):
                    log(
                        "INCOMING FROM TOPIC: %(topic)s partition %(message_partition)s HEADERS: %(headers)s DATA: %(incoming_data)s",
                        params={log_const.KEY_NAME: "incoming_message",
                                "topic": mq_message.topic,
                                "message_partition": mq_message.partition,
                                "message_key": mq_message.key,
                                "kafka_key": kafka_key,
                                "incoming_data": str(message.masked_value),
                                "headers": str(mq_message.headers)})

                    db_uid = message.db_uid

                    span = jaeger_utils.get_incoming_spam(self.tracer, message, mq_message)

                    with self.tracer.scope_manager.activate(span, True) as scope:
                        with StatsTimer() as load_timer:
                            user = self.load_user(db_uid, message)

                    with self.tracer.scope_manager.activate(span, True) as scope:
                        with self.tracer.start_span('Loading time', child_of=scope.span) as span:
                            smart_kit_metrics.sampling_load_time(self.app_name, load_timer.secs)
                            with StatsTimer() as script_timer:
                                commands = self.model.answer(message, user)

                        with self.tracer.start_span('Script time', child_of=scope.span) as span:
                            answers = self._generate_answers(user=user, commands=commands, message=message,
                                                             topic_key=topic_key,
                                                             kafka_key=kafka_key)
                            smart_kit_metrics.sampling_script_time(self.app_name, script_timer.secs)

                        with self.tracer.start_span('Saving time', child_of=scope.span) as span:
                            with StatsTimer() as save_timer:
                                user_save_no_collisions = self.save_user(db_uid, user, message)

                        smart_kit_metrics.sampling_save_time(self.app_name, save_timer.secs)
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

                    if mq_message.headers is None:
                        mq_message.headers =[]
                    self.tracer.inject(span_context=span.context, format=jaeger_kafka_codec.KAFKA_MAP,
                                       carrier=list(mq_message.headers))

                    if answers:
                        return answers

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
                            "message_key": mq_message.key,
                            "message_partition": mq_message.partition,
                            "kafka_key": kafka_key,
                            "uid": user.id,
                            "db_version": str(user.variables.get(user.USER_DB_VERSION))},
                    level="WARNING")

                smart_kit_metrics.counter_save_collision_tries_left(self.app_name)
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
                            kafka_key: kafka_key},
                    level="ERROR", exc_info=True)
            except Exception:
                log("Error handling worker fail exception.",
                    level="ERROR", exc_info=True)

    def iterate_behavior_timeouts(self):
        answers = []
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

                    orig_message_raw = json.loads(mq_message.value)
                    orig_message_raw[SmartAppFromMessage.MESSAGE_NAME] = message_names.LOCAL_TIMEOUT

                    timeout_from_message = self._get_timeout_from_message(orig_message_raw, callback_id,
                                                                          headers=mq_message.headers)

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
                                    "message_key": mq_message.key,
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
                                "message_key": mq_message.key,
                                "message_partition": mq_message.partition,
                                "kafka_key": kafka_key,
                                "uid": user.id,
                                "db_version": str(user.variables.get(user.USER_DB_VERSION))},
                        level="WARNING")

                    smart_kit_metrics.counter_save_collision_tries_left(self.app_name)
                self.save_behavior_timeouts(user, mq_message, kafka_key)
                if answers:
                    return answers
            except:
                log("%(class_name)s error.", params={log_const.KEY_NAME: "error_handling_timeout",
                                                     "class_name": self.__class__.__name__,
                                                     log_const.REQUEST_VALUE: str(mq_message.value)},
                    level="ERROR", exc_info=True)
