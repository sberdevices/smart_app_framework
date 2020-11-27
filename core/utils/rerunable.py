import core.logging.logger_constants as log_const
from core.logging.logger_utils import log
from core.monitoring.monitoring import monitoring


class Rerunable():
    DEFAULT_RERUNABLE_TRY_COUNT = 5

    def __init__(self, config=None):
        self.config = config or {}
        self.try_count = self.config.get("try_count") or self.DEFAULT_RERUNABLE_TRY_COUNT

    @property
    def _handled_exception(self):
        raise NotImplementedError

    def _on_prepare(self):
        raise NotImplementedError

    def _on_all_tries_fail(self):
        raise NotImplementedError

    def _run(self, action, *args, _try_count=None, **kwargs):
        if _try_count is None:
            _try_count = self.try_count
        if _try_count <= 0:
            self._on_all_tries_fail()
        _try_count = _try_count - 1
        try:
            result = action(*args, **kwargs)
        except self._handled_exception as e:
            params = {
                "class_name": str(self.__class__),
                "exception": str(e),
                "try_count": _try_count,
                log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE
            }
            log("%(class_name)s run failed with %(exception)s.\n Got %(try_count)s tries left.",
                          params=params,
                          level="ERROR")
            self._on_prepare()
            result = self._run(action, *args, _try_count=_try_count, **kwargs)
            counter_name = self._get_counter_name()
            if counter_name:
                monitoring.got_counter(f"{counter_name}_exception")
        return result

    def _get_counter_name(self):
        return
