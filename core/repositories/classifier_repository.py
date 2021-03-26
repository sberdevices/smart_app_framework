import os
from typing import Callable, Any, Dict

import tensorflow as tf
from keras.utils import CustomObjectScope

import scenarios.logging.logger_constants as scenarios_log_const
from core.basic_models.classifiers.basic_classifiers import SkipClassifier
from core.basic_models.classifiers.classifiers_constants import REQUIRED_CONFIG_PARAMS, SUPPORTED_CLASSIFIERS_TYPES
from core.logging.logger_utils import log
from core.repositories.base_repository import BaseRepository
from core.repositories.dill_repository import DillRepository
from core.repositories.folder_repository import FolderRepository


class ClassifierRepository(BaseRepository):

    def __init__(self, description_path: str, data_path: str, loader: Callable, source: str, *args, **kwargs) -> None:
        super(ClassifierRepository, self).__init__(source=source, *args, **kwargs)
        self._description_path = description_path
        self._data_path = data_path
        self._folder_repository = FolderRepository(self._description_path, loader, source, *args, **kwargs)
        self._required_classifier_config_params = REQUIRED_CONFIG_PARAMS
        self._supported_classifiers_types = SUPPORTED_CLASSIFIERS_TYPES

    def _subfolder_data_path(self, filename: str) -> str:
        return os.path.join(self._data_path, filename)

    def _check_classifier_config(self, classifier_key: str, classifier_params: Dict[str, Any]) -> None:
        for req_param in self._required_classifier_config_params:
            try:
                classifier_params[req_param]
            except KeyError:
                raise Exception(f"Missing field: '{req_param}' for classifier {classifier_key} in classifiers.json")

    def load(self) -> None:
        self._folder_repository.load()
        classifiers_dict = self._folder_repository.data

        gpu_available = tf.test.is_gpu_available()
        channel = os.environ.get("CHANNEL")
        repository = None

        for classifier_key in classifiers_dict:
            classifier_params = classifiers_dict[classifier_key]
            self._check_classifier_config(classifier_key, classifier_params)

            permitted_channels = classifier_params["channels"]
            # Не грузить модель если текущий канал не в списке релевантных каналов классификатора
            if channel and permitted_channels and channel not in permitted_channels:
                continue

            # Не грузить модель если она для gpu, но доступных gpu нет
            if classifier_params.get("is_gpu") and gpu_available is False:
                continue

            classifier_type = classifier_params["type"]
            if classifier_type not in self._supported_classifiers_types:
                log(
                    message=f"classifier_repository.load: Invalid classifier type for classifier "
                            f"%({scenarios_log_const.CLASSIFIER_VALUE})s",
                    params={scenarios_log_const.KEY_NAME: scenarios_log_const.STARTUP_VALUE,
                            scenarios_log_const.CLASSIFIER_VALUE: classifier_key},
                    level='WARN'
                )
                classifiers_dict[classifier_key] = SkipClassifier.get_nothing()
                continue

            # Нечего загружать тк в конфигурациях этих классификаторов модель не предусматривается
            if classifier_type in ["skip", "external"]:
                continue

            if classifier_type == "default" and "text_normalizer" not in classifier_params:
                continue

            custom_layers = classifier_params.get("custom_layers", dict())
            if custom_layers:
                # Загрузка кастомных слоев, нужных для keras моделей
                try:
                    for layer in custom_layers:
                        layer_repository = DillRepository(self._subfolder_data_path(layer["path"]), self.source)
                        layer_repository.load()
                        custom_layers[layer["layer_name"]] = layer_repository.data
                except FileNotFoundError:
                    log(
                        message=f"classifier_repository.load: Failed to load custom layers for "
                        f"classifier %({scenarios_log_const.CLASSIFIER_VALUE})s, file not found",
                        params={scenarios_log_const.KEY_NAME: scenarios_log_const.STARTUP_VALUE,
                                scenarios_log_const.CLASSIFIER_VALUE: classifier_key},
                        level="WARN"
                    )
                    classifiers_dict[classifier_key] = SkipClassifier.get_nothing()
                    continue

            if classifier_type in ["scikit"]:
                repository = DillRepository(self._subfolder_data_path(classifier_params["path"]), self.source)

            log(
                message=f"classifier_repository.load: loading %({scenarios_log_const.CLASSIFIER_VALUE})s classifier",
                params={scenarios_log_const.KEY_NAME: scenarios_log_const.STARTUP_VALUE,
                        scenarios_log_const.CLASSIFIER_VALUE: classifier_key}
            )

            try:
                with CustomObjectScope(custom_layers):
                    repository.load()
                classifier_params["classifier"] = repository.data
            except FileNotFoundError:
                log(
                    message=f"classifier_repository.load: Failed to load classifier "
                            f"%({scenarios_log_const.CLASSIFIER_VALUE})s, file not found",
                    params={scenarios_log_const.KEY_NAME: scenarios_log_const.STARTUP_VALUE,
                            scenarios_log_const.CLASSIFIER_VALUE: classifier_key},
                    level="WARN"
                )
                classifiers_dict[classifier_key] = SkipClassifier.get_nothing()

        super(ClassifierRepository, self).fill(classifiers_dict)

    def save(self, save_parameters: Any) -> None:
        pass
