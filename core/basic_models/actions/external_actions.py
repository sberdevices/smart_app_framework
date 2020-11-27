from typing import Optional, Dict, Any, Union, List

from core.model.base_user import BaseUser

from core.basic_models.actions.command import Command
from core.text_preprocessing.base import BaseTextPreprocessingResult

from core.basic_models.actions.basic_actions import action_factory
from core.basic_models.actions.basic_actions import CommandAction
from core.descriptions.smart_updatable_lazy_descriptions import SmartUpdatableLazyDescriptions


class ExternalActions(SmartUpdatableLazyDescriptions):
    def __init__(self, items):
        super(ExternalActions, self).__init__(action_factory, items)


class ExternalAction(CommandAction):
    version: Optional[int]
    command: str
    action: str

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(ExternalAction, self).__init__(items, id)
        self._action_key = items["action"]

    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        action = user.descriptions["external_actions"][self._action_key]
        commands = action.run(user, text_preprocessing_result, params)
        return commands
