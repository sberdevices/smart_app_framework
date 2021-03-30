import concurrent.futures
import os
import time
import threading

from confluent_kafka.cimpl import KafkaException
from core.message.from_message import SmartAppFromMessage

import scenarios.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.utils.stats_timer import StatsTimer
from smart_kit.start_points.main_loop_kafka import MainLoop as KafkaMainLoop


class ParallelKafkaMainLoop(KafkaMainLoop):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_workers = self.settings["template_settings"].get("max_workers", (os.cpu_count() or 1) * 5)
        self.pool = self.get_pool()
        self._tasks = []
        self._step = self.settings["template_settings"].get("ml_step", 0.05)  # seconds
        self._locks = {}
        log(
            "%(class_name)s started with %(workers)s workers.",
            params={
                log_const.KEY_NAME: log_const.STARTUP_VALUE, "class_name": self.__class__.__name__,
                "workers": self.max_workers,
            }
        )

    def get_pool(self) -> concurrent.futures.Executor:
        return concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)

    def pre_handle(self):
        super().pre_handle()

        free_slots = self.max_workers > len(self._tasks)
        if not free_slots:
            for task in list(self._tasks):
                if task.done():
                    self._tasks.remove(task)
            time.sleep(self._step)

    def run(self):
        super().run()
        self.pool.shutdown()

    def process_message(self, mq_message, consumer, kafka_key, stats):
        # ну тут чутка копипасты
        mutex = None
        try:
            message_value = mq_message.value()
            message = SmartAppFromMessage(message_value,
                                          headers=mq_message.headers(),
                                          masking_fields=self.masking_fields)
            if message.validate():
                mutex = self._locks.setdefault(message.db_uid, threading.Lock())
                mutex.acquire()

            super().process_message(mq_message, consumer, kafka_key, stats)
        except Exception:
            if mutex and mutex.locked():
                mutex.release()
            raise
        if mutex and mutex.locked():
            mutex.release()

    def iterate(self, kafka_key):
        consumer = self.consumers[kafka_key]

        with StatsTimer() as poll_timer:
            try:
                mq_message = None
                message_value = None
                for mq_message in consumer.consume(self.max_workers - len(self._tasks)):
                    message_value = mq_message.value()
                    task = self.pool.submit(self.process_message, mq_message, consumer, kafka_key, "")
                    self._tasks.append(task)

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

        stats = "Polling time: {} msecs\n".format(poll_timer.msecs)
        log(stats)
