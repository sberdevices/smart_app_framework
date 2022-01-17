import logging
from unittest import TestCase
from unittest.mock import Mock

from core.logging.logger_utils import log


class TestLogger(TestCase):

    def test_escaping(self):
        # используем здесь мок, потому что ошибка
        # пишется в консоль, но не рейсится наружу
        fh = logging.StreamHandler()
        logging.root.handlers = []
        logging.root.addHandler(fh)
        fh.handleError = Mock()

        log("%0", level="ERROR")
        self.assertEqual(fh.handleError.called, False)

    def test_render_params(self):
        fh = logging.StreamHandler()
        logging.root.handlers = []
        logging.root.addHandler(fh)
        fh.stream.write = Mock()
        log("%(p)s %p %p", level="ERROR", params={'p': 'value'})
        self.assertEqual(fh.stream.write.call_args[0][0], 'value %p %p\n')
