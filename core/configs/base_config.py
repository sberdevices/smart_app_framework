import os
from typing import List

from core.model.registered import Registered
from core.repositories.base_repository import BaseRepository


class BaseConfig:
    def __init__(self, **kwargs):
        self.registered_repositories = Registered()
        self.repositories = []
        self.source = kwargs.get("source")

    def __getitem__(self, key):
        return self.registered_repositories[key].data

    def get(self, key, default=None):
        return self.registered_repositories[key].data if key in self.registered_repositories else default

    @property
    def _subfolder(self):
        raise NotImplementedError

    def subfolder_path(self, filename):
        return os.path.join(self._subfolder, filename)

    def init(self):
        self.init_repositories()

    def init_repositories(self):
        for rep in self.repositories:
            rep.load()
            self.registered_repositories[rep.key] = rep

    def raw(self):
        items = self.registered_repositories
        return {key: items[key].data for key in items}

    def _override_repositories(self, main_rep: List[BaseRepository], new_repo: List[BaseRepository]) -> List[BaseRepository]:
        """
        Метод предназначе для переопределения источников для чтения по умолчанию на
        пользовательские
        :param main_rep: Переопределяемый список репозиториев
        :param new_repo: Список замен
        :return: Переопределённый список репозиториев
        """
        temp_dict = dict()
        for el in main_rep:
            temp_dict[el.key] = el

        for el in new_repo:
            temp_dict[el.key] = el

        result = []
        for key, value in temp_dict.items():
            result.append(value)

        return result
