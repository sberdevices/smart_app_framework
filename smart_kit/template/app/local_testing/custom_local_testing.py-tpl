from smart_kit.testing.local import CLInterface


class CustomLocalTesting(CLInterface):
    """
      Тут модифицируется local_testing для эмулирования ответов от внешних систем
      формат функции - on_<message_name>(self, message):
      где <message_name> - это тип сообщения,написанный в нижнем регистре
      например:
        def on_back_get_token_request(self, message):
          # BACK_GET_TOKEN_REQUEST - тип сообщения
          return json.dumps({
            "messageId": self.environment.message_id,
            "messageName": "BACK_GET_TOKEN_RESPONSE",
            "uuid": {
              "userChannel": self.environment.user_channel,
              "userId": self.environment.user_id,
              "chatId": self.environment.chat_id
            },
            "payload": {
              "token": "test",
            }
           }
          )
  """
