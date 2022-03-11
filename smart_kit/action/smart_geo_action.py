from typing import Dict, Any, Optional, Union, List

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.model.base_user import BaseUser
from core.text_preprocessing.base import BaseTextPreprocessingResult
from smart_kit.names.message_names import GET_PROFILE_DATA


class SmartGeoAction(StringAction):
    def run(self, user: BaseUser, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> List[Command]:
        commands = [Command(GET_PROFILE_DATA)]
        return commands
