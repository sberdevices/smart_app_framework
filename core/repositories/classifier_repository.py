import os

import tensorflow as tf
from keras.utils import CustomObjectScope

import scenarios.logging.logger_constants as scenarios_log_const
from core.basic_models.classifiers.basic_classifiers import SkipClassifier
from core.logging.logger_utils import log
from core.repositories.base_repository import BaseRepository
from core.repositories.dill_repository import DillRepository
from core.repositories.folder_repository import FolderRepository


class ClassifierRepository(BaseRepository):

    def __init__(self, description_path, data_path, loader, source, *args, **kwargs):
        super(ClassifierRepository, self).__init__(source=source, *args, **kwargs)
        self._description_path = description_path
        self._data_path = data_path
        self._folder_repository = FolderRepository(self._description_path, loader, source, *args, **kwargs)

    def _subfolder_data_path(self, filename):
        return os.path.join(self._data_path, filename)

    def load(self):
        # TODO refactor: вместо if использовать зарегестрированные фабрики - Кристина

        self._folder_repository.load()
        classifiers_dict = self._folder_repository.data
        gpu_available = tf.test.is_gpu_available()
        channel = os.environ.get("CHANNEL")

        for key in classifiers_dict:
            try:
                permitted_channels = classifiers_dict[key]["channels"]
            except KeyError:
                raise Exception("Missing field: 'channels'!")

            if channel and permitted_channels and channel not in permitted_channels:
                continue

            # Не грузить модельку если она для gpu, но доступных gpu нет
            if classifiers_dict[key].get("is_gpu") and gpu_available is False:
                continue

            if classifiers_dict[key]["type"] == "default" and "text_normalizer" not in classifiers_dict[key]:
                continue

            if classifiers_dict[key]["type"] in ["skip", "external"]:
                continue

            custom_layers = {}
            if "custom_layers" in classifiers_dict[key]:
                # Загрузка кастомных слоев, нужных для keras моделей
                try:
                    for layer in classifiers_dict[key].get("custom_layers", []):
                        layer_repository = DillRepository(self._subfolder_data_path(layer["path"]),
                                                          self.source)
                        layer_repository.load()
                        custom_layers[layer["layer_name"]] = layer_repository.data
                except FileNotFoundError:
                    log(f'classifier_repository.load: Failed to load custom layers for '
                               f'classifier %({scenarios_log_const.CLASSIFIER_VALUE})s, file not found',
                               {scenarios_log_const.KEY_NAME: scenarios_log_const.STARTUP_VALUE,
                                scenarios_log_const.CLASSIFIER_VALUE: key}, level='WARN')
                    classifiers_dict[key] = SkipClassifier.get_nothing()
                    continue

            if classifiers_dict[key]["type"] in {'meta', 'structured',
                                                 'sklearn_description_classifier'}:
                repository = DillRepository(self._subfolder_data_path(classifiers_dict[key]["path"]), self.source)
            elif classifiers_dict[key]["type"] == "pavlov":
                raise Exception("Sorry, models based on deeppavlov are not supported yet!")
            else:
                log(f'classifier_repository.load: Invalid classifier type for '
                           f'classifier %({scenarios_log_const.CLASSIFIER_VALUE})s',
                           {scenarios_log_const.KEY_NAME: scenarios_log_const.STARTUP_VALUE,
                            scenarios_log_const.CLASSIFIER_VALUE: key}, level='WARN')
                classifiers_dict[key] = SkipClassifier.get_nothing()
                continue

            log(f"classifier_repository.load: "
                       f"loading %({scenarios_log_const.CLASSIFIER_VALUE})s classifier",
                       {scenarios_log_const.KEY_NAME: scenarios_log_const.STARTUP_VALUE,
                        scenarios_log_const.CLASSIFIER_VALUE: key})
            try:
                with CustomObjectScope(custom_layers):
                    repository.load()
                classifiers_dict[key]["classifier"] = repository.data
            except FileNotFoundError:
                log(f'classifier_repository.load: Failed to load '
                           f'classifier %({scenarios_log_const.CLASSIFIER_VALUE})s, file not found',
                           {scenarios_log_const.KEY_NAME: scenarios_log_const.STARTUP_VALUE,
                            scenarios_log_const.CLASSIFIER_VALUE: key}, level='WARN')
                classifiers_dict[key] = SkipClassifier.get_nothing()
        super(ClassifierRepository, self).fill(classifiers_dict)

    def save(self, save_parameters):
        pass
