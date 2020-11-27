import logging
from typing import List, Tuple, Optional

from confluent_kafka.cimpl import Message
from jaeger_client import SpanContext
from jaeger_client.codecs import TextCodec
from jaeger_client.constants import TRACE_ID_HEADER, BAGGAGE_HEADER_PREFIX, DEBUG_ID_HEADER_KEY, BAGGAGE_HEADER_KEY

KAFKA_MAP = "kafka_map"


class KafkaCodec(TextCodec):
    """
    Кодек предназначен для серилизации/десерелизации трейса в/из заголовок(а) кафки
    """
    VALUE_POS = 1
    KEY_POS = 0
    ENCODING = 'utf-8'

    def __init__(self,
                 url_encoding=False,
                 trace_id_header=TRACE_ID_HEADER,
                 baggage_header_prefix=BAGGAGE_HEADER_PREFIX,
                 debug_id_header=DEBUG_ID_HEADER_KEY,
                 baggage_header=BAGGAGE_HEADER_KEY):

        super().__init__(url_encoding, trace_id_header, baggage_header_prefix, debug_id_header, baggage_header)

        self.target_keys = {self.trace_id_header, self.baggage_prefix, self.debug_id_header, self.baggage_header}
        self.__logger = logging.getLogger(__name__)

    def inject(self, span_context, carrier: List[Tuple[str, bytes]]):
        if carrier is None:
            carrier = []
        existing_keys = {}
        for pos, el in enumerate(carrier):
            existing_keys[el[KafkaCodec.KEY_POS]] = pos

        carrier_dict = {}
        super().inject(span_context, carrier_dict)

        for key, value in carrier_dict.items():
            if key in existing_keys:
                carrier[existing_keys[key]] = (key, value.encode(KafkaCodec.ENCODING))
            else:
                carrier.append((key, value.encode(KafkaCodec.ENCODING)))

    def extract(self, carrier: Message) -> Optional[SpanContext]:
        header = carrier.headers()
        header_dict = {}
        if header:
            for el in header:
                if el[KafkaCodec.KEY_POS] in self.target_keys:
                    header_dict[el[KafkaCodec.KEY_POS]] = el[KafkaCodec.VALUE_POS].decode(KafkaCodec.ENCODING)
        span_context: SpanContext = None
        try:
            span_context = super().extract(header_dict)
        except Exception:
            self.__logger.exception("Could not extract SpanContext. Using new one")

        return span_context
