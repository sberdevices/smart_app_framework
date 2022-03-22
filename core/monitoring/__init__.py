from core.monitoring import monitoring


def init_monitoring(monitoring_class):
    if not isinstance(monitoring.monitoring, monitoring_class):
        monitoring.monitoring = monitoring_class()
