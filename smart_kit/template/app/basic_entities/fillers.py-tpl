# coding: utf-8
from typing import Dict, Optional, Any

from core.text_preprocessing.preprocessing_result import TextPreprocessingResult
from core.utils.exception_handlers import exc_handler

from scenarios.scenario_models.field.field_filler_description import FieldFillerDescription
from scenarios.user.user_model import User


class CustomFieldFiller(FieldFillerDescription):

    """
        Тут можно создать собственные Fillers для использования их в заполнении полей форм и
    """

    def __init__(self, items: Optional[Dict[str, Any]], id: Optional[str] = None) -> None:
        super(SampleFieldFiller, self).__init__(items, id)
        items = items or {}
        self.test_item = items.get("test_item")

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: TextPreprocessingResult, user: User, params) -> Optional[str]:
        return None
