from lazy import lazy

from core.message.from_message import SmartAppFromMessage
from smart_kit.message.smartapp_to_message import SmartAppToMessage


class SmartAppRtdmToMessage(SmartAppToMessage):

    @lazy
    def as_dict(self):
        self.incoming_message: SmartAppFromMessage
        fields = {
           "messageId": self.incoming_message.incremental_id,
           "userChannel": self.incoming_message.channel,
           "userId": self.incoming_message.uid,
        }
        fields.update(self.command.payload)
        fields.update(self.root_nodes)
        return fields
