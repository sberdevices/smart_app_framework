from typing import Optional, Union, List, Dict, Any

from lazy import lazy

import core.logging.logger_constants as log_const
from core.model.factory import factory, list_factory
from core.basic_models.actions.basic_actions import RequirementAction, ChoiceAction, ElseAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.exception_handlers import exc_handler
from core.logging.logger_utils import log

from scenarios.scenario_models.field.field_filler_description import FieldFillerDescription
from scenarios.user.user_model import User


class RequirementFiller(RequirementAction):

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(RequirementFiller, self).__init__(items, id)
        self._item = items["filler"]

    @lazy
    @factory(FieldFillerDescription)
    def internal_item(self):
        return self._item

    def on_extract_error(self, text_preprocessing_result, user):
        log("exc_handler: RequirementFiller failed to extract. Return None. MESSAGE: {}.".format(user.message.masked_value),
            user, {log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE}, level="ERROR", exc_info=True)
        return None

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult,
                user: User) -> Optional[Union[int, float, str, bool, List, Dict]]:
        return self.run(user, text_preprocessing_result)


class ChoiceFiller(ChoiceAction):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(ChoiceFiller, self).__init__(items, id)
        self._requirement_items = items["requirement_fillers"]
        self._else_item = items.get("else_filler")

    @lazy
    @list_factory(RequirementFiller)
    def items(self):
        return self._requirement_items

    @lazy
    @factory(FieldFillerDescription)
    def else_item(self):
        return self._else_item

    def on_extract_error(self, text_preprocessing_result, user):
        log("exc_handler: ChoiceFiller failed to extract. Return None. MESSAGE: {}.".format(user.message.masked_value),
            user,
            {log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE}, level="ERROR", exc_info=True)
        return None

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult,
                user: User) -> Optional[Union[int, float, str, bool, List, Dict]]:
        return self.run(user, text_preprocessing_result)


class ElseFiller(ElseAction):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(ElseFiller, self).__init__(items, id)
        self._item = items["filler"]
        self._else_item = items.get("else_filler")

    @lazy
    @factory(FieldFillerDescription)
    def item(self):
        return self._item

    @lazy
    @factory(FieldFillerDescription)
    def else_item(self):
        return self._else_item

    def on_extract_error(self, text_preprocessing_result, user):
        log("exc_handler: ElseFiller failed to extract. Return None. MESSAGE: {}.".format(user.message.masked_value),
            user,
            {log_const.KEY_NAME: log_const.HANDLED_EXCEPTION_VALUE}, level="ERROR", exc_info=True)
        return None

    @exc_handler(on_error_obj_method_name="on_extract_error")
    def extract(self, text_preprocessing_result: BaseTextPreprocessingResult,
                user: User) -> Optional[Union[int, float, str, bool, List, Dict]]:
        return self.run(user, text_preprocessing_result)
