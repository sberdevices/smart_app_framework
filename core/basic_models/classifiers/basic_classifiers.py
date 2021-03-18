from typing import Any, Dict, Optional, Union, List

from timeout_decorator import timeout_decorator

import core.basic_models.classifiers.classifiers_constants as cls_const
from core.model.factory import build_factory
from core.model.registered import Registered
from core.text_preprocessing.base import BaseTextPreprocessingResult
from core.utils.exception_handlers import exc_handler

classifiers = Registered()

classifier_factory = build_factory(classifiers)


class Classifier:

    SCORE_KEY = cls_const.SCORE_KEY
    ANSWER_KEY = cls_const.ANSWER_KEY
    CLASS_OTHER = cls_const.OTHER_KEY

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        self.id = id
        self.items = items or {}
        self.version = items.get("version", -1)
        self.threshold = self.items.get("threshold", 0)
        self._intents = self.items.get("intents", {})
        self.score_key = self.SCORE_KEY
        self.answer_key = self.ANSWER_KEY
        self.class_other = self.CLASS_OTHER

    def _answer_template(self, intent: str, score: float, is_other: bool) -> Dict[str, Union[str, float, bool]]:
        # Любой классификатор должен возвращать отсортированный список наиболее вероятных вариантов из заданного
        # множества, прошедших определенный порог уверенности. Каждый вариант из списка должен соответвовать общему
        # шаблону: answer=классу, score=величине уверенности в ответе, other=булево значение (принадлежность к other).
        return {self.answer_key: intent, self.score_key: score, self.class_other: is_other}

    def find_best_answer(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            mask: Optional[Dict[str, bool]] = None,
            classifiers_param=None,
            vectorizers_param=None
    ) -> List[Dict[str, Union[str, float, bool]]]:
        raise NotImplementedError

    def initial_launch(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            classifiers_param=None,
            vectorizers_param=None
    ):
        raise NotImplementedError


class SkipClassifier(Classifier):

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(SkipClassifier, self).__init__(items, id)
        self._intents = self.items["intents"]

    def find_best_answer(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            mask: Optional[Dict[str, bool]] = None,
            classifiers_param=None,
            vectorizers_param=None
    ) -> List[Dict[str, Union[str, float, bool]]]:
        return [self._answer_template(intent, 0, False) for intent in self._intents]

    def initial_launch(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            classifiers_param=None,
            vectorizers_param=None
    ):
        pass

    @staticmethod
    def get_nothing() -> Dict[str, Any]:
        return {"type": "skip", "intents": []}


class ExternalClassifier(Classifier):

    # Дефолтное значение таймаута, время за которое должен прийти ответ от внешнего классификатора
    BLOCKING_TIMEOUT = cls_const.EXTERNAL_CLASSIFIER_BLOCKING_TIMEOUT

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None) -> None:
        super(ExternalClassifier, self).__init__(items, id)
        if items.get("type") != "external":
            raise Exception("Classifier type should be 'external' here!")
        self._classifier_key = items["classifier"]
        self._timeout_wrap = timeout_decorator.timeout(self.items.get("timeout") or self.BLOCKING_TIMEOUT)

    @exc_handler(handled_exceptions=(timeout_decorator.TimeoutError,), on_error_return_res=[])
    def find_best_answer(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            mask: Optional[Dict[str, bool]] = None,
            classifiers_param=None,
            vectorizers_param=None
    ) -> List[Dict[str, Union[str, float, bool]]]:
        classifier = classifiers_param[self._classifier_key]
        return self._timeout_wrap(classifier.find_best_answer)(
            text_preprocessing_result, mask, classifiers_param, vectorizers_param)

    def initial_launch(
            self,
            text_preprocessing_result: BaseTextPreprocessingResult,
            classifiers_param=None,
            vectorizers_param=None
    ):
        classifier = classifiers_param[self._classifier_key]
        return classifier.initial_launch(text_preprocessing_result, classifiers_param, vectorizers_param)
