# coding: utf-8
from typing import Optional, Dict, Any

from core.basic_models.requirement.basic_requirements import Requirement
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult

from scenarios.user.user_model import User


class CustomRequirement(Requirement):

    """
        Тут можно создать собственные Requirements для использования их в сценариях
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(CustomRequirement, self).__init__(items, id)
        items = items or {}
        self.test_param = items.get("test_param")

    def check(self, text_preprocessing_result: TextPreprocessingResult,
              user: User, params: Dict[str, Any] = None) -> bool:
        return False
