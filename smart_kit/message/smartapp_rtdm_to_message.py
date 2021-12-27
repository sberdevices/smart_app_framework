from lazy import lazy

from core.message.from_message import SmartAppFromMessage
from smart_kit.message.smartapp_to_message import SmartAppToMessage


class SmartAppRtdmToMessage(SmartAppToMessage):

    @lazy
    def as_dict(self):
        self.incoming_message: SmartAppFromMessage
        fields = {
           "messageId": self.incoming_message.incremental_id,
           "messageName": self.payload["messageName"],
           "userChannel": self.payload["userChannel"],
           "nextSystem": self.payload["nextSystem"],
           "handlerName": self.payload["handlerName"],
           "userId": self.payload["userId"],
           "chatId": self.payload["chatId"],
           "notificationId": self.payload["notificationId"],
           "notificationCode": self.payload["notificationCode"],
           "feedbackStatus": self.payload["feedbackStatus"],
           "description": self.payload["description"]
        }
        fields.update(self.root_nodes)
        return fields
