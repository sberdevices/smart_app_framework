from typing import Dict, Any, Optional, List, Union

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from scenarios.user.user_model import User


class CallRatingAction(StringAction):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        items["command"] = "CALL_RATING"
        super().__init__(items, id)

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self.request_data = {
            "topic_key": "toDP",
            "kafka_key": "main",
            "kafka_replyTopic": user.settings["template_settings"]["consumer_topic"]
        }

        return super().run(user, text_preprocessing_result, params)


class AskRatingAction(StringAction):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        items["command"] = "ASK_RATING"
        super().__init__(items, id)

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self.request_data = {
            "topic_key": "toDP",
            "kafka_key": "main",
            "kafka_replyTopic": user.settings["template_settings"]["consumer_topic"]
        }

        return super().run(user, text_preprocessing_result, params)
