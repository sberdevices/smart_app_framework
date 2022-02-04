from typing import Dict, Any, Optional, Union, List

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.pickle_copy import pickle_deepcopy
from scenarios.user.user_model import User

GIVE_ME_MEMORY = "GIVE_ME_MEMORY"
REMEMBER_THIS = "REMEMBER_THIS"
KAFKA = "kafka"


class GiveMeMemoryAction(StringAction):

    """
    example: {
        "type": "give_me_memory",
        "behavior": "client_info_request",
        "nodes": {
            "memory": {
                "confidentialMemo": [
                    "userAgreement"
                ],
                "projectPrivateMemo": [
                    "character_{{message.uuid.userId}}"
                ]
            },
            "profileEmployee": {
                "type": "unified_template",
                "template": "{{ example }}"
                "loader": "json"
            },
            "tokenType": {
                "type": "unified_template",
                "template": "{{ example }}",
                "loader": "json"
            }
        }
    }
    """

    DEFAULT_KAFKA_KEY = "main"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        items["command"] = GIVE_ME_MEMORY
        super().__init__(items, id)
        self.request_type = KAFKA
        self.behavior = items.get("behavior")
        self._nodes["root_nodes"] = {"protocolVersion": 1}
        self._nodes["memory"] = [
            {"memoryPartition": key, "tags": val} for key, val in self._nodes["memory"].items()
        ]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self._nodes["consumer"] = {"projectId": user.settings["template_settings"]["project_id"]}

        self.request_data = {
            "topic_key": "client_info",
            "kafka_key": self.DEFAULT_KAFKA_KEY,
            "kafka_replyTopic": user.settings["template_settings"]["consumer_topic"]
        }

        if self.behavior:
            scenario_id = user.last_scenarios.last_scenario_name
            user.behaviors.add(user.message.generate_new_callback_id(), self.behavior, scenario_id,
                               text_preprocessing_result.raw, action_params=pickle_deepcopy(params))

        commands = super().run(user, text_preprocessing_result, params)
        return commands


class RememberThisAction(StringAction):

    """
    example: {
        "type": "remember",
        "nodes": {
          "clientIds": {
            "type": "unified_template",
            "template": "{{ example }}"
            "loader": "json"
          },
          "memory": [
            {
              "memoryPartition": "publicMemo",
              "partitionData": [
                {
                  "tag": "historyInfo",
                  "action": {
                    "type": "upsert",
                    "params": {
                      "operation": [
                        {
                          "selector": {
                            "intent": {
                              "$eq": "run_app"
                            },
                            "surface": {
                              "$eq": "{{ example }}"
                            },
                            "channel": {
                              "$eq": "{{ channel }}"
                            },
                            "projectId": {
                              "$eq": "{{current_app_info.project_id|default(\"\")}}"
                            }
                          },
                          "updater": [
                            {
                              "$set": {
                                "$.lastExecuteDateTime": "{{now()|strftime('%Y-%m-%d %H:%M:%S')}}"
                              }
                            },
                            {
                              "$inc": {
                                "$.executeCounter": 1
                              }
                            }
                          ]
                        }
                      ]
                    }
                  }
                }
              ]
            }
          ]
        }
    }
    """

    DEFAULT_KAFKA_KEY = "main"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        items["command"] = REMEMBER_THIS
        super().__init__(items, id)
        self.request_type = KAFKA
        self._nodes["root_nodes"] = {"protocolVersion": 3}

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self._nodes["consumer"] = {"projectId": user.settings["template_settings"]["project_id"]}

        self.request_data = {
            "topic_key": "client_info_remember",
            "kafka_key": self.DEFAULT_KAFKA_KEY,
            "kafka_replyTopic": user.settings["template_settings"]["consumer_topic"]
        }

        commands = super().run(user, text_preprocessing_result, params)
        return commands
