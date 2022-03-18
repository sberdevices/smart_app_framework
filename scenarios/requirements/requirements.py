# coding: utf-8
import re

from core.basic_models.requirement.basic_requirements import Requirement
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.unified_template.unified_template import UnifiedTemplate
from scenarios.user.user_model import User
from typing import Optional, Dict, Any


class AskAgainExistRequirement(Requirement):

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
              params: Dict[str, Any] = None) -> bool:
        last_scenario_id = user.last_scenarios.last_scenario_name
        scenario = user.descriptions["scenarios"].get(last_scenario_id)
        return scenario.check_ask_again_requests(text_preprocessing_result, user, params)


class TemplateInArrayRequirement(Requirement):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(TemplateInArrayRequirement, self).__init__(items, id)
        self._template = UnifiedTemplate(items["template"])
        self._items = set(items["items"])

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
              params: Dict[str, Any] = None) -> bool:
        params = params or {}
        collected = user.parametrizer.collect(text_preprocessing_result)
        params.update(collected)
        render_result = self._template.render(params)
        return render_result in self._items


class ArrayItemInTemplateRequirement(Requirement):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(ArrayItemInTemplateRequirement, self).__init__(items, id)
        self._template = UnifiedTemplate(items["template"])
        self._items = set(items["items"])

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
              params: Dict[str, Any] = None) -> bool:
        params = params or {}
        collected = user.parametrizer.collect(text_preprocessing_result)
        params.update(collected)
        render_result = self._template.render(params)
        for item in self._items:
            if item in render_result:
                return True
        return False


class RegexpInTemplateRequirement(Requirement):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(RegexpInTemplateRequirement, self).__init__(items, id)
        self._template = UnifiedTemplate(items["template"])
        self._regexp = re.compile(items["regexp"], re.S | re.M)

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: User,
              params: Dict[str, Any] = None) -> bool:
        params = params or {}
        collected = user.parametrizer.collect(text_preprocessing_result)
        params.update(collected)
        render_result = self._template.render(params)
        return True if self._regexp.search(render_result) else False
