from lazy import lazy

from scenarios.user.user_model import User

from .parametrizer import CustomParametrizer


class CustomeUser(User):

    """
        Класс User - модель для хранения данных конкретного пользователя
        в метод fields можно добавляются собственные поля, для использования внутри базовых сущностей
    """

    def __init__(self, id, message, db_data, settings, descriptions, parametrizer_cls, load_error=False):
        super(CustomeUser, self).__init__(id, message, db_data, settings,
                                         descriptions, parametrizer_cls, load_error)

    @property
    def fields(self):
        return super(CustomeUser, self).fields + []

    @lazy
    def parametrizer(self):
        return CustomParametrizer(self, {})

    def expire(self):
        super(CustomeUser, self).expire()
