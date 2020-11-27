from smart_kit.models.smartapp_model import SmartAppModel


class CustomModel(SmartAppModel):

    """
        В собственной Model можно добавить новые хендлеры для обработки входящих сообщений
    """

    def __init__(self, resources, dialogue_manager_cls, custom_settings, **kwargs):
        super(CustomModel, self).__init__(resources, dialogue_manager_cls, custom_settings, **kwargs)
        self._handlers.update({})

