from lazy import lazy

from core.message.from_message import SmartAppFromMessage
from smart_kit.message.smartapp_to_message import SmartAppToMessage


class SmartAppPushToMessage(SmartAppToMessage):

    @lazy
    def as_dict(self):
        self.incoming_message: SmartAppFromMessage
        fields = {
            "projectId": self.payload.get("project_id"),
            "clientId": self.incoming_message.sub,
            "surface": self.payload.get("surface"),
            "content": self.payload.get("content"),
        }
        fields.update(self.root_nodes)
        return fields

