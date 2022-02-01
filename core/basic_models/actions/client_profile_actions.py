from typing import Dict, Any, Optional, Union, List

from core.basic_models.actions.command import Command
from core.basic_models.actions.string_actions import StringAction
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.pickle_copy import pickle_deepcopy
from scenarios.user.user_model import User

GIVE_ME_MEMORY = "GIVE_ME_MEMORY"
REMEMBER_THIS = "REMEMBER_THIS"


class GiveMeMemoryAction(StringAction):

    """
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
    """

    DEFAULT_KAFKA_KEY = "main"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        self.behavior = items.get("behavior")
        self._nodes["root_nodes"] = {"protocolVersion": 1}
        items["command"] = GIVE_ME_MEMORY
        super().__init__(items, id)

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self._nodes["consumer"] = {"projectId": user.settings["template_settings"]["project_id"]}

        memory_info = self._nodes["memory"].copy()
        self._nodes["memory"] = []
        for key, val in memory_info.items():
            self._nodes["memory"].append({"memoryPartition": key, "tags": val})

        self.request_data = {
            "topic_key": "client_info",
            "kafka_key": self.DEFAULT_KAFKA_KEY,
            "kafka_replyTopic": user.settings["template_settings"]["consumer_topic"]
        }

        if self.behavior:
            scenario_id = user.last_scenarios.last_scenario_name
            user.behaviors.add(user.message.generate_new_callback_id(), self.behavior, scenario_id,
                               text_preprocessing_result.raw, action_params=pickle_deepcopy(params))

        command_params = self._generate_command_context(user, text_preprocessing_result, params)

        commands = [
            Command(self.command, command_params, self.id, request_type="kafka", request_data=self.request_data)
        ]
        return commands


class RememberThisAction(StringAction):

    """
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
    """

    DEFAULT_KAFKA_KEY = "main"

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        self._nodes["root_nodes"] = {"protocolVersion": 3}
        items["command"] = REMEMBER_THIS
        super().__init__(items, id)

    def run(self, user: User, text_preprocessing_result: BaseTextPreprocessingResult,
            params: Optional[Dict[str, Union[str, float, int]]] = None) -> Optional[List[Command]]:
        self._nodes["consumer"] = {"projectId": user.settings["template_settings"]["project_id"]}
        self._nodes["root_nodes"] = {"protocolVersion": user.message.protocolVersion}

        self.request_data = {
            "topic_key": "client_info_remember",
            "kafka_key": self.DEFAULT_KAFKA_KEY,
            "kafka_replyTopic": user.settings["template_settings"]["consumer_topic"]
        }

        command_params = self._generate_command_context(user, text_preprocessing_result, params)

        commands = [
            Command(self.command, command_params, self.id, request_type="kafka", request_data=self.request_data)
        ]
        return commands
