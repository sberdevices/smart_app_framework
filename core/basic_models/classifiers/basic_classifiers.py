import inspect
import pickle
import sys
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List

import numpy as np
from lazy import lazy
from timeout_decorator import timeout_decorator

import core.basic_models.classifiers.classifiers_constants as cls_const
from core.basic_models.classifiers.vectorizer_models import vectorizers
from core.model.factory import build_factory
from core.model.registered import Registered
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.exception_handlers import exc_handler

classifiers = Registered()

classifier_factory = build_factory(classifiers)


class Classifier(ABC):
    """Базовый класс для сущности Классификатор."""

    CLASSIFIER_TYPE = None

    def __init__(self, settings: Dict[str, Any], id: Optional[str] = None) -> None:
        self.id = id
        self.settings = settings if settings else {}
        self.version = settings.get("version", -1)
        self.threshold = self.settings.get("threshold", 0)
        self.intents = self.settings.get("intents", [])
        self.class_other = cls_const.OTHER_KEY
        self._check_classifier_type(settings["type"])

    def _answer_template(self, intent: str, score: float, is_other: bool) -> Dict[str, Union[str, float, bool]]:
        # Любой классификатор должен возвращать отсортированный список наиболее вероятных вариантов из заданного
        # множества, прошедших определенный порог уверенности. Каждый вариант из списка должен соответвовать общему
        # шаблону: answer=классу, score=величине уверенности в ответе, other=булево значение (принадлежность к other).
        return {cls_const.ANSWER_KEY: intent, cls_const.SCORE_KEY: score, self.class_other: is_other}

    def _check_classifier_type(self, classifier_type: str) -> None:
        if classifier_type != self.CLASSIFIER_TYPE:
            raise Exception(f"Inappropriate classifier type: {classifier_type}, it should be {self.CLASSIFIER_TYPE}")

    @abstractmethod
    def find_best_answer(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            mask: Optional[Dict[str, bool]] = None,
            scenario_classifiers: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Union[str, float, bool]]]:
        # Формируется отсортированный список наиболее вероятных вариантов
        raise NotImplementedError

    @abstractmethod
    def initial_launch(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            scenario_classifiers: Optional[Dict[str, Any]] = None
    ) -> Union[List[Dict[str, Union[str, float, bool]]], None]:
        # Первоначальный запуск модели классификатора
        raise NotImplementedError


class SkipClassifier(Classifier):
    """
    Классификатор, который не делает (пропускает) сам процесс классификации.
    Используется, когда необходимо по формату указать классификатор, но использовать конкретное значение-результат.
    """

    CLASSIFIER_TYPE = "skip"

    def __init__(self, settings: Dict[str, Any], id: Optional[str] = None) -> None:
        super(SkipClassifier, self).__init__(settings, id)
        self.intents = self.settings["intents"]

    def find_best_answer(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            mask: Optional[Dict[str, bool]] = None,
            scenario_classifiers: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Union[str, float, bool]]]:
        return [self._answer_template(intent, 0, False) for intent in self.intents]

    def initial_launch(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            scenario_classifiers: Optional[Dict[str, Any]] = None
    ) -> Union[List[Dict[str, Union[str, float, bool]]], None]:
        pass

    @staticmethod
    def get_nothing() -> Dict[str, Any]:
        return {"type": "skip", "intents": []}


class ExternalClassifier(Classifier):
    """Внешний классификатор.
    Выполняет некую функцию обёртки для вызова реализованных классов классификаторов по имени.
    """

    # Дефолтное значение таймаута, время за которое должен прийти ответ от внешнего классификатора
    BLOCKING_TIMEOUT = cls_const.EXTERNAL_CLASSIFIER_BLOCKING_TIMEOUT
    CLASSIFIER_TYPE = "external"

    def __init__(self, settings: Dict[str, Any], id: Optional[str] = None) -> None:
        super(ExternalClassifier, self).__init__(settings, id)
        self._classifier_key = settings["classifier"]
        self._timeout_wrap = timeout_decorator.timeout(self.settings.get("timeout") or self.BLOCKING_TIMEOUT)

    @exc_handler(on_error_obj_method_name="on_timeout_error", handled_exceptions=(timeout_decorator.TimeoutError,))
    def find_best_answer(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            mask: Optional[Dict[str, bool]] = None,
            scenario_classifiers: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Union[str, float, bool]]]:
        classifier = scenario_classifiers[self._classifier_key]
        return self._timeout_wrap(classifier.find_best_answer)(text_preprocessing_result, mask, scenario_classifiers)

    @staticmethod
    def on_timeout_error(*args, **kwarg):
        return list()

    def initial_launch(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            scenario_classifiers: Optional[Dict[str, Any]] = None
    ):
        classifier = scenario_classifiers[self._classifier_key]
        return classifier.initial_launch(text_preprocessing_result, scenario_classifiers)


class ExtendedClassifier(Classifier):
    """Класс не является самостоятельным типом классификатора. Расширяет функционал базового класса."""

    def __init__(self, settings: Dict[str, Any], id: Optional[str] = None) -> None:
        super(ExtendedClassifier, self).__init__(settings, id)
        self.intents = self.settings["intents"]
        self._path = self.settings["path"]
        self._classifier = self.settings.get("classifier")
        # Способ векторизации для реплик указывается в конфигурации классификатора
        self._vectorizer = self.settings.get("vectorizer")

    def set_classifier(self, clsf: Classifier) -> None:
        self._classifier = clsf

    @lazy
    def classifier(self) -> Classifier:
        return self._classifier

    def find_best_answer(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            mask: Optional[Dict[str, bool]] = None,
            scenario_classifiers: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Union[str, float, bool]]]:
        vector = vectorizers[self._vectorizer].vectorize(text_preprocessing_result) if self._vectorizer else np.array([])
        weights = sorted(self._get_weights(text_preprocessing_result, vector).items(), key=lambda x: x[1], reverse=True)
        answers = []
        for weight in weights:
            if weight[0] < len(self.intents):
                cls_name = self.intents[weight[0]]
                cls_prob = weight[1]
                answers.append(self._answer_template(cls_name, cls_prob, cls_name == self.class_other))
        return answers

    def _get_weights(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            vector: Optional[np.ndarray] = np.array([]),
            numb: int = 3
    ):
        weights = self._prediction(text_preprocessing_result, vector)
        tuple_weights = sorted(
            {i: weight for i, weight in enumerate(weights) if weight >= self.threshold}.items(),
            key=lambda x: x[1],
            reverse=True
        )
        tuple_weights = tuple_weights[:numb]  # берем numb наибольших значений весов
        return dict(tuple_weights)

    @abstractmethod
    def _prediction(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            vector: Optional[np.ndarray] = np.array([])
    ) -> List[Any]:
        raise NotImplementedError

    def initial_launch(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            scenario_classifiers: Optional[Dict[str, Any]] = None
    ) -> Union[List[Dict[str, Union[str, float, bool]]], None]:
        return self.find_best_answer(text_preprocessing_result, None, classifiers)


class SciKitClassifier(ExtendedClassifier):
    """Класс для загрузки и инфера моделей обученных с помощью библиотеки sklearn и имеющих тип scikit.
    У сохраненного класса обученной модели предполагается обязательное наличие метода predict_proba.
    """

    CLASSIFIER_TYPE = "scikit"

    def __init__(self, settings: Dict[str, Any], id: Optional[str] = None) -> None:
        super(SciKitClassifier, self).__init__(settings, id)

    @staticmethod
    def prepared(text_preprocessing_result: BaseTextPreprocessingResult):
        return pickle.dumps(text_preprocessing_result.tokenized_elements_list)

    def _prediction(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            vector: Optional[np.ndarray] = np.array([])
    ) -> List[Any]:
        if vector.size != 0:
            prediction_result = self.classifier.predict_proba(
                self.prepared(text_preprocessing_result), vector)[0].tolist()
        else:
            prediction_result = self.classifier.predict_proba(self.prepared(text_preprocessing_result))[0].tolist()
        return prediction_result


# Реализованные на данный момент типы классификаторов
SUPPORTED_CLASSIFIERS_TYPES = frozenset([
    class_tuple[1].CLASSIFIER_TYPE
    for class_tuple in inspect.getmembers(sys.modules[__name__], inspect.isclass)
    if hasattr(class_tuple[1], "CLASSIFIER_TYPE") and class_tuple[1].CLASSIFIER_TYPE
])
