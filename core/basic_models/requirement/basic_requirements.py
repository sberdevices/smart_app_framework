# coding: utf-8
import hashlib

from datetime import datetime, timezone
from random import random
from lazy import lazy
from typing import List, Optional, Dict, Any

from croniter import croniter

import core.logging.logger_constants as log_const
from core.basic_models.operators.operators import Operator
from core.logging.logger_utils import log
from core.model.base_user import BaseUser
from core.model.factory import build_factory, list_factory, factory
from core.model.registered import Registered
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate

requirements = Registered()

requirement_factory = build_factory(requirements)


class Requirement:
    # should_process_message compatible
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        items = items or {}
        self.items = items
        self.version = items.get("version", -1)
        self.id = id

    def _log_params(self):
        return {
            log_const.KEY_NAME: log_const.REQUIREMENT_CHECK_VALUE,
            "requirement": self.__class__.__name__
        }

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        return True

    def on_check_error(self, text_preprocessing_result, user):
        log("exc_handler: Requirement failed to check. Return False. MESSAGE: {}.".format(user.message.masked_value),
            user, {log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE},
            level="ERROR", exc_info=True)
        return False


class CompositeRequirement(Requirement):
    requirements: List[Requirement]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(CompositeRequirement, self).__init__(items, id)
        self._requirements = items["requirements"]

    @lazy
    @list_factory(Requirement)
    def requirements(self):
        return self._requirements


class AndRequirement(CompositeRequirement):

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        return all(requirement.check(text_preprocessing_result=text_preprocessing_result, user=user, params=params)
                   for requirement in self.requirements)


class OrRequirement(CompositeRequirement):

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        return any(requirement.check(text_preprocessing_result=text_preprocessing_result, user=user, params=params)
                   for requirement in self.requirements)


class NotRequirement(Requirement):
    requirement: Requirement

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(NotRequirement, self).__init__(items, id)
        self._requirement = items["requirement"]

    @lazy
    @factory(Requirement)
    def requirement(self):
        return self._requirement

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        return not self.requirement.check(text_preprocessing_result=text_preprocessing_result, user=user, params=params)


class ComparisonRequirement(Requirement):
    operator: Operator

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(ComparisonRequirement, self).__init__(items, id)
        self._operator = items["operator"]

    @lazy
    @factory(Operator)
    def operator(self):
        return self._operator


class RandomRequirement(Requirement):
    percent: int

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(RandomRequirement, self).__init__(items, id)
        self.percent = items["percent"]

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        result = random() * 100
        return result < self.percent


class TopicRequirement(Requirement):
    topics: List[str]

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(TopicRequirement, self).__init__(items, id)
        self.topics = items["topics"]

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        return user.message.topic_key in self.topics


class TemplateRequirement(Requirement):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(TemplateRequirement, self).__init__(items, id)
        self._template = UnifiedTemplate(items["template"])

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        params = params or {}
        collected = user.parametrizer.collect(text_preprocessing_result)
        params.update(collected)
        render_result = self._template.render(params)
        if render_result == "True":
            return True
        if render_result == "False":
            return False
        raise TypeError(f'Template result should be "True" or "False", got: ',
                        f'{render_result} for template {self.items["template"]}')


class RollingRequirement(Requirement):
    percent: int

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(RollingRequirement, self).__init__(items, id)
        self.percent = items["percent"]

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        id = user.id
        s = id.encode('utf-8')
        hash = int(hashlib.sha256(s).hexdigest(), 16)
        res = hash % 100
        return res < self.percent


class TimeRequirement(ComparisonRequirement):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)

    def check(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            user: BaseUser,
            params: Dict[str, Any] = None
    ) -> bool:
        message_time_dict = user.message.payload['meta']['time']
        message_timestamp_sec = message_time_dict['timestamp'] // 1000
        message_time = datetime.fromtimestamp(message_timestamp_sec, tz=timezone.utc).time()
        return self.operator.compare(message_time)

    @lazy
    @factory(Operator)
    def operator(self):
        operator = dict(self._operator)
        amount_time = datetime.strptime(operator["amount"], '%H:%M:%S').time()
        operator["amount"] = amount_time
        return operator


class DateTimeRequirement(Requirement):
    match_cron: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super().__init__(items, id)
        self.match_cron = items['match_cron']

    def check(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            user: BaseUser,
            params: Dict[str, Any] = None
    ) -> bool:
        message_time_dict = user.message.payload['meta']['time']
        message_timestamp_sec = message_time_dict['timestamp'] // 1000
        message_datetime = datetime.fromtimestamp(message_timestamp_sec)
        return croniter.match(self.match_cron, message_datetime)
