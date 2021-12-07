# coding: utf-8
from core.model.base_user import BaseUser
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from core.utils.utils import convert_version_to_list_of_int
from lazy import lazy
from typing import List, Optional, Dict, Any

from core.model.factory import factory

from core.basic_models.requirement.basic_requirements import Requirement, ComparisonRequirement
from core.basic_models.operators.operators import Operator
from core.text_preprocessing.base import BaseTextPreprocessingResult


class BaseContainsRequirement(Requirement):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(BaseContainsRequirement, self).__init__(items)

    @property
    def descr_to_check_in(self):
        return NotImplementedError

    def get_field(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser):
        return NotImplementedError

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        return self.get_field(text_preprocessing_result, user) in self.descr_to_check_in


class ChannelRequirement(BaseContainsRequirement):
    channels = List[str]

    # should_process_message compatible
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(ChannelRequirement, self).__init__(items, id)
        self.channels = items["channels"]

    @property
    def descr_to_check_in(self):
        return set(self.channels)

    def get_field(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser) -> str:
        return user.message.channel


class PlatformTypeRequirement(Requirement):

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(PlatformTypeRequirement, self).__init__(items, id)
        items = items or {}
        self.platfrom_type = items["platfrom_type"]

    def check(self, text_preprocessing_result: TextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        return user.message.device.platform_type == self.platfrom_type


class BasicVersionRequirement(ComparisonRequirement):

    @factory(Operator)
    def build_operator(self):
        operator = dict(self._operator)
        operator["amount"] = convert_version_to_list_of_int(operator["amount"])
        return operator


class PlatformVersionRequirement(BasicVersionRequirement):

    def check(self, text_preprocessing_result: TextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        platform_version = convert_version_to_list_of_int(user.message.device.platform_version)
        return self.operator.compare(platform_version) if platform_version is not None else False


class SurfaceRequirement(Requirement):

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(SurfaceRequirement, self).__init__(items, id)
        items = items or {}
        self.surface = items["surface"]

    def check(self, text_preprocessing_result: TextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        return user.message.device.surface == self.surface


class SurfaceVersionRequirement(BasicVersionRequirement):

    def check(self, text_preprocessing_result: TextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        surface_version = convert_version_to_list_of_int(user.message.device.surface_version)
        return self.operator.compare(surface_version) if surface_version is not None else False


class AppTypeRequirement(Requirement):

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(AppTypeRequirement, self).__init__(items, id)
        items = items or {}
        self.app_type = items["app_type"]

    def check(self, text_preprocessing_result: TextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        return self.app_type in user.message.device.features.get("appTypes", [])


class CapabilitiesPropertyAvailableRequirement(Requirement):

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(CapabilitiesPropertyAvailableRequirement, self).__init__(items, id)
        items = items or {}
        self.property_type = items["property_type"]

    def check(self, text_preprocessing_result: TextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        return user.message.device.capabilities.get(self.property_type, {}).get("available", False)
