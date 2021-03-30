from prometheus_client import multiprocess
from prometheus_client import generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST

# Expose metrics.
def application(env, start_response):
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    data = generate_latest(registry)
    status = '200 OK'
    response_headers = [
        ('Content-type', CONTENT_TYPE_LATEST),
        ('Content-Length', str(len(data)))
    ]
    start_response(status, response_headers)
    return iter([data])
