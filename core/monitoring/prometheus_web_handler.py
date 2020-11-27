import io
import time
from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client.twisted import MetricsResource
from twisted.web.resource import Resource
from core.monitoring.twisted_server import TwistedServer
from core.utils.memstats import get_meminfo, show_growth, show_most_common_types, get_leaking_objects


def add_headers(request, response_text):
    request.responseHeaders.addRawHeader(b"content-type", CONTENT_TYPE_LATEST.encode())
    request.responseHeaders.addRawHeader(b"content-length", str(len(response_text)).encode())


class RootResource(Resource):

    def __init__(self, debug=False):
        super(RootResource, self).__init__()
        self.putChild(b'health', HealthcheckResource())
        self.putChild(b'metrics', MetricsResource())

        if debug:
            self.putChild(b'meminfo', MemInfoResource())
            self.putChild(b'objgrowth', ObjGrowthResource())
            self.putChild(b'objtypes', ObjTypesResource())
            self.putChild(b'objleak', ObjLeakResource())

    def getChild(self, name, request):
        if name:
            return Resource.getChild(self, name, request)
        return self

    def render_GET(self, request):
        response = ""
        add_headers(request, response)
        return response.encode()


class HealthcheckResource(Resource):
    isLeaf = True

    def render_GET(self, request):
        response = "ok"
        add_headers(request, response)
        return response.encode()


class MemInfoResource(Resource):
    isLeaf = True

    def render_GET(self, request):
        response = get_meminfo()
        add_headers(request, response)
        return response.encode()


class ObjGrowthResource(Resource):
    isLeaf = True

    def render_GET(self, request):
        with io.StringIO() as tempio:
            show_growth(file=tempio)
            response = tempio.getvalue()

        add_headers(request, response)
        return response.encode()


class ObjTypesResource(Resource):
    isLeaf = True

    def render_GET(self, request):
        with io.StringIO() as tempio:
            show_most_common_types(file=tempio, limit=20)
            response = tempio.getvalue()
        add_headers(request, response)
        return response.encode()


class ObjLeakResource(Resource):
    isLeaf = True

    def render_GET(self, request):
        with io.StringIO() as tempio:
            get_leaking_objects(file=tempio, limit=5)
            response = tempio.getvalue()
        add_headers(request, response)
        return response.encode()


if __name__ == "__main__":
    t = TwistedServer(1111, "localhost", RootResource, debug=True)
    while 1:
        t.iterate()
        time.sleep(1)