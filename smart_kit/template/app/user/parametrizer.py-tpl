from scenarios.user.parametrizer import Parametrizer


class CustomParametrizer(Parametrizer):

    """
        Тут можно добавить новые данные, которые будут доступны для использования в ASL при использовании jinja
    """

    def __init__(self, user, items):
        super(CustomParametrizer, self).__init__(user, items)

    def _get_user_data(self, text_preprocessing_result=None):
        data = super(CustomParametrizer, self)._get_user_data(text_preprocessing_result)
        data.update({})
        return data
