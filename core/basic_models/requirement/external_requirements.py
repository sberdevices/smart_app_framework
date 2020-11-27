from typing import Dict, Any, Optional

from core.basic_models.requirement.basic_requirements import Requirement, requirement_factory
from core.model.base_user import BaseUser

from core.text_preprocessing.base import BaseTextPreprocessingResult

from core.descriptions.smart_updatable_lazy_descriptions import SmartUpdatableLazyDescriptions


class ExternalRequirements(SmartUpdatableLazyDescriptions):
    def __init__(self, items):
        super(ExternalRequirements, self).__init__(requirement_factory, items, ordered=True)


class ExternalRequirement(Requirement):
    requirement: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(ExternalRequirement, self).__init__(items, id)
        self.requirement = items["requirement"]

    def check(self, text_preprocessing_result: BaseTextPreprocessingResult, user: BaseUser,
              params: Dict[str, Any] = None) -> bool:
        requirement = user.descriptions["external_requirements"][self.requirement]
        return requirement.check(text_preprocessing_result, user, params)
