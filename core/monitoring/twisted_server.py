from twisted.internet import reactor
from twisted.web import server
from core.logging.logger_utils import log
import core.logging.logger_constants as log_const


class TwistedServer:
    def __init__(self, port, interface, handler, debug=False):
        log("TwistedServer.__init__ started.", params={log_const.KEY_NAME: log_const.TWISTED_SERVER},
                      level="WARNING")
        site = server.Site(handler(debug=debug))
        reactor.listenTCP(port, site, interface=interface or "")
        reactor.startRunning(False)
        log("TwistedServer.__init__ finished.", params={log_const.KEY_NAME: log_const.TWISTED_SERVER},
                      level="WARNING")

    def iterate(self):
        reactor.iterate()
