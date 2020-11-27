import logging

from jaeger_client import Config, ConstSampler
from jaeger_client.reporter import NullReporter

from core.jaeger_custom_client.kafka_codec import KafkaCodec, KAFKA_MAP


class ExtendedConfig(Config):
    """
    Конфиг расширяет базовый класс, вводя поддержку KafkaCodec и возможность отключать трасировку
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def initialize_tracer(self, io_loop=None):
        """
        Initialize Jaeger Tracer based on the passed `jaeger_client.Config`.
        Save it to `opentracing.tracer` global variable.
        Only the first call to this method has any effect.
        """

        with Config._initialized_lock:
            if Config._initialized:
                self.logger.warning('Jaeger tracer already initialized, skipping')
                return
            Config._initialized = True

        if self.enabled:
            tracer = self.new_tracer(io_loop)
        else:
            reporter = NullReporter()
            sampler = ConstSampler(False)
            tracer = self.create_tracer(reporter, sampler, None)

        self._initialize_global_tracer(tracer=tracer)
        return tracer

    @property
    def propagation(self):
        codec = KafkaCodec(url_encoding=False,
                           trace_id_header=self.trace_id_header,
                           baggage_header_prefix=self.baggage_header_prefix,
                           debug_id_header=self.debug_id_header)
        return {KAFKA_MAP: codec}
