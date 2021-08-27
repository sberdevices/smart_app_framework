import os
from collections import OrderedDict
from typing import Callable, Any, Dict

import tensorflow as tf
from keras.utils.generic_utils import CustomObjectScope

import scenarios.logging.logger_constants as scenarios_log_const
from core.basic_models.classifiers.basic_classifiers import SkipClassifier, SciKitClassifier, ExternalClassifier, \
    SUPPORTED_CLASSIFIERS_TYPES
from core.basic_models.classifiers.classifiers_constants import REQUIRED_CONFIG_PARAMS
from core.logging.logger_utils import log
from core.repositories.base_repository import BaseRepository
from core.repositories.dill_repository import DillRepository
from core.repositories.folder_repository import FolderRepository
from core.text_preprocessing.preprocessing_result import TextPreprocessingResult

CLASSIFIER_TYPES_MAP = OrderedDict({"scikit": SciKitClassifier, "skip": SkipClassifier, "external": ExternalClassifier})


def classifiers_initial_launch(classifiers: Dict[str, Any]) -> None:
    # external классификаторы должны запускаться последними
    type_order = [_type for _type in CLASSIFIER_TYPES_MAP]
    sorted_cls_by_type_order = OrderedDict(sorted(classifiers.items(), key=lambda i: type_order.index(i[1]["type"])))

    text_preprocessing_result = TextPreprocessingResult({})
    for cls_name, cls_settings in sorted_cls_by_type_order.items():
        cls = CLASSIFIER_TYPES_MAP[cls_settings["type"]](cls_settings)
        cls.initial_launch(text_preprocessing_result, sorted_cls_by_type_order)
        sorted_cls_by_type_order[cls_name] = cls


class ClassifierRepository(BaseRepository):

    def __init__(self, description_path: str, data_path: str, loader: Callable, source: str, *args, **kwargs) -> None:
        super(ClassifierRepository, self).__init__(source=source, *args, **kwargs)
        self._description_path = description_path
        self._data_path = data_path
        self._required_classifier_config_params = REQUIRED_CONFIG_PARAMS
        self._supported_classifiers_types = SUPPORTED_CLASSIFIERS_TYPES
        self._folder_repository = FolderRepository(
            self._description_path, loader, source, *args, **kwargs) if self._check_paths_existence() else None

    def _subfolder_data_path(self, filename: str) -> str:
        return os.path.join(self._data_path, filename)

    def _check_paths_existence(self) -> bool:
        res = False
        # Проверяем что существуют обе директории: с конфигами классификаторов и чекпоинтами моделей,
        # также проверяем что эти обе директории не пустые
        if (os.path.exists(self._description_path) and len(os.listdir(self._description_path))
                and os.path.exists(self._data_path) and len(os.listdir(self._data_path))):
            res = True
        return res

    def _check_classifier_config(self, classifier_key: str, classifier_params: Dict[str, Any]) -> None:
        for req_param in self._required_classifier_config_params:
            try:
                classifier_params[req_param]
            except KeyError:
                raise Exception(f"Missing field: '{req_param}' for classifier {classifier_key} in classifiers.json")

    def load(self) -> None:
        if not self._folder_repository:
            return None

        self._folder_repository.load()
        classifiers_dict = self._folder_repository.data

        gpu_available = tf.test.is_gpu_available()
        repository = None

        for classifier_key in classifiers_dict:
            classifier_params = classifiers_dict[classifier_key]
            self._check_classifier_config(classifier_key, classifier_params)

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
        classifiers_initial_launch(classifiers_dict)

    def save(self, save_parameters: Any) -> None:
        pass
