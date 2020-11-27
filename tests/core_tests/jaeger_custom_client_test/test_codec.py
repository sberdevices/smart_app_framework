import unittest
from unittest.mock import Mock

from core.jaeger_custom_client.kafka_codec import KafkaCodec

NLP_BAGGAGE = "nlp-baggage-"

NLP_TRACE_ID = "nlp-trace-id"


class KafkaCodecTest(unittest.TestCase):

    def setUp(self) -> None:
        self.codec = KafkaCodec(trace_id_header=NLP_TRACE_ID, baggage_header_prefix=NLP_BAGGAGE)

    def test_extract(self):
        # Won't fail if there is a filter in KafkaCode extract method
        trace_id = 15441712733567627997
        span_id = 957657810971653503
        parent_id = 0
        flags = 1

        header = [('d', b'D'), ('cp', b'\xff'), ("b'0xc9'", b'0xc9'), ('q', b''), ('a', b'g '),
                  (NLP_TRACE_ID, b'd64bfbeadfecb2dd:d4a48b48757f57f:0:1')]
        carrier = Mock()
        carrier.headers.return_value = header

        actual = self.codec.extract(carrier)
        self.assertEqual(actual.trace_id, trace_id)
        self.assertEqual(actual.span_id, span_id)
        self.assertIsNone(actual.parent_id)
        self.assertEqual(actual.flags, flags)

    def test_extract_with_malformed_trace_id(self):
        header = [('d', b'D'), ('cp', b'\xff'), ("b'0xc9'", b'0xc9'), ('q', b''), ('a', b'g '),
                  (NLP_TRACE_ID, b'this_is_malformed_trace_id')]
        carrier = Mock()
        carrier.headers.return_value = header

        actual = self.codec.extract(carrier)
        self.assertIsNone(actual)

    def test_inject(self):
        span_context = Mock()
        span_context.trace_id = 15441712733567627997
        span_context.span_id = 957657810971658888
        span_context.parent_id = 957657810971653503
        span_context.flags = 1
        span_context.baggage = {"some_key": "56"}
        baggage_key = f"{NLP_BAGGAGE}test"
        header = [('d', b'D'), ('cp', b'\xff'), ("b'0xc9'", b'0xc9'), ('q', b''),
                  (NLP_TRACE_ID, b'd64bfbeadfecb2dd:d4a48b48757f57f:0:1'), ('a', b'g '),
                  (baggage_key, b'test_data')]

        expected_header = [('d', b'D'), ('cp', b'\xff'), ("b'0xc9'", b'0xc9'), ('q', b''),
                           (NLP_TRACE_ID, b'd64bfbeadfecb2dd:d4a48b487580a88:d4a48b48757f57f:1'), ('a', b'g '),
                           (baggage_key, b'test_data'),
                           (f"{NLP_BAGGAGE}some_key", b"56")]
        self.codec.inject(span_context, header)
        self.assertSequenceEqual(expected_header, header)


