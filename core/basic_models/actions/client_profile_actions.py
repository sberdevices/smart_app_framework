from typing import Dict, Any, Optional, Union, List

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.pickle_copy import pickle_deepcopy
from scenarios.user.user_model import User
from core.configs.global_constants import KAFKA

GIVE_ME_MEMORY = "GIVE_ME_MEMORY"
REMEMBER_THIS = "REMEMBER_THIS"


class GiveMeMemoryAction(StringAction):

    """
    Example::
        {
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
                    "template": "{{ 0 }}",
                    "loader": "json"
                },
                "tokenType": {
                    "type": "unified_template",
                    "template": "{{ 0 }}",
                    "loader": "json"
                }
            }
        }
    """

    DEFAULT_KAFKA_KEY = "main"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super().__init__(items, id)
        self.command = GIVE_ME_MEMORY
        self.request_type = KAFKA
        self.kafka_key = items.get("kafka_key")
        self.behavior = items.get("behavior")
        self._nodes["root_nodes"] = {"protocolVersion": items.get("protocolVersion") or 1}
        self._nodes["memory"] = [
            {"memoryPartition": key, "tags": val} for key, val in self._nodes["memory"].items()
        ]

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self._nodes["consumer"] = {"projectId": user.settings["template_settings"]["project_id"]}

        settings_kafka_key = user.settings["template_settings"].get("client_profile_kafka_key")
        self.request_data = {
            "topic_key": "client_info",
            "kafka_key": self.kafka_key or settings_kafka_key or self.DEFAULT_KAFKA_KEY,
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
    Example::
      {
        "type": "remember",
        "nodes": {
          "clientIds": {
            "type": "unified_template",
            "template": "{{ 0 }}",
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
                              "$eq": "{{ 0 }}"
                            },
                            "channel": {
                              "$eq": "{{ 0 }}"
                            },
                            "projectId": {
                              "$eq": "{{ 0 }}"
                            }
                          },
                          "updater": [
                            {
                              "$set": {
                                "$.lastExecuteDateTime": "{{ 0 }}"
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
        super().__init__(items, id)
        self.command = REMEMBER_THIS
        self.request_type = KAFKA
        self.kafka_key = items.get("kafka_key")
        self._nodes["root_nodes"] = {"protocolVersion": items.get("protocolVersion") or 3}

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self._nodes["consumer"] = {"projectId": user.settings["template_settings"]["project_id"]}

        settings_kafka_key = user.settings["template_settings"].get("client_profile_kafka_key")
        self.request_data = {
            "topic_key": "client_info_remember",
            "kafka_key": self.kafka_key or settings_kafka_key or self.DEFAULT_KAFKA_KEY,
            "kafka_replyTopic": user.settings["template_settings"]["consumer_topic"]
        }

        commands = super().run(user, text_preprocessing_result, params)
        return commands
