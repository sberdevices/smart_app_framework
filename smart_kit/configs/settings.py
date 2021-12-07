import yaml
import os

from core.configs.base_config import BaseConfig
from core.db_adapter.ceph.ceph_adapter import CephAdapter
from core.db_adapter.os_adapter import OSAdapter
from core.repositories.file_repository import UpdatableFileRepository, FileRepository


class Settings(BaseConfig):
    CephAdapterKey = "ceph"
    OSAdapterKey = "os"

    def __init__(self, *args, **kwargs):
        super(Settings, self).__init__()
        self.configs_path = kwargs.get("config_path")
        self.references_path = kwargs.get("references_path")
        self.secret_path = kwargs.get("secret_path")
        self.app_name = kwargs.get("app_name")
        self.adapters = {Settings.CephAdapterKey: CephAdapter, self.OSAdapterKey: OSAdapter}
        self.repositories = [
            UpdatableFileRepository(
                self.subfolder_path("template_config.yml"), loader=yaml.safe_load, key="template_settings"
            ),
            FileRepository(self.subfolder_secret_path("kafka_config.yml"), loader=yaml.safe_load, key="kafka"),
            FileRepository(
                self.subfolder_path("ceph_config.yml"), loader=yaml.safe_load, key=self.CephAdapterKey
            ),
            FileRepository(self.subfolder_path("aiohttp.yml"), loader=yaml.safe_load, key="aiohttp"),
        ]
        self.repositories = self.override_repositories(self.repositories)
        self.init()

    def init(self):
        super().init()
        update_time = self["template_settings"].get("config_update_cooldown")
        if update_time is not None:
            for repo in self.repositories:
                if isinstance(repo, UpdatableFileRepository):
                    repo.update_cooldown = update_time

    def override_repositories(self, repositories: list):
        """
        Метод предназначен для переопределения репозиториев в дочерних классах.
        :param repositories: Список репозиториев родителя
        :return: Переопределённый в наследниках список репозиториев
        """
        return repositories

    @property
    def _subfolder(self):
        return self.configs_path

    def subfolder_secret_path(self, filename):
        return os.path.join(self.secret_path, filename)

    def get_source(self):
        adapter_key = self.registered_repositories["template_settings"].data.get(
            "data_adapter") or Settings.OSAdapterKey
        adapter_settings = self.registered_repositories[
            adapter_key].data if adapter_key != Settings.OSAdapterKey else None
        adapter = self.adapters[adapter_key](adapter_settings)
        adapter.connect()
        source = adapter.source
        return source
