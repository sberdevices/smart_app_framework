# coding: utf-8
from typing import Union, Dict, Any, Optional

from core.basic_models.actions.basic_actions import Action
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult

from scenarios.user.user_model import User


class CustomAction(Action):

    """
        Тут можно создать собственные Actions для использования их в сценариях
    """

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(CustomAction, self).__init__(items, id)
        items = items or {}
        self.test_param = items.get("test_param")

    def run(self, user: User, text_preprocessing_result: TextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> None:
        print("Test Action")
        return None
