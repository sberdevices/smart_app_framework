from unittest import TestCase
from unittest.mock import Mock, patch

from core.basic_models.classifiers.basic_classifiers import ExternalClassifier
from scenarios.scenario_models.field.field_filler_description import ClassifierFiller, ClassifierFillerMeta


class TestClassifierFiller(TestCase):

    def setUp(self):
        test_items = {
            "type": "classifier",
            "intents": ["да", "нет"],
            "classifier": {"type": "external", "classifier": "hello_scenario_classifier"}
        }
        self.filler = ClassifierFiller(test_items)

        self.mock_text_preprocessing_result = Mock()
        self.mock_user = Mock()
        self.mock_user.descriptions = {
            "external_classifiers": ["read_book_or_not_classifier", "hello_scenario_classifier"]}

    @patch.object(
        ExternalClassifier,
        "find_best_answer",
        return_value=[{"answer": "нет", "score": 0.7, "other": False}, {"answer": "да", "score": 0.3, "other": False}]
    )
    def test_filler_extract(self, mock_classifier_model):
        """Тест кейз проверяет что поле заполнено наиболее вероятным значением, которое вернула модель."""
        expected_res = "нет"
        actual_res = self.filler.extract(self.mock_text_preprocessing_result, self.mock_user)
        self.assertEqual(expected_res, actual_res)

    @patch.object(ExternalClassifier, "find_best_answer", return_value=[])
    def test_filler_extract_if_no_model_answer(self, mock_classifier_model):
        """Тест кейз проверяет что поле осталось не заполненным те результат None, если модель не выдала ответ."""
        actual_res = self.filler.extract(self.mock_text_preprocessing_result, self.mock_user)
        self.assertIsNone(actual_res)


class TestClassifierFillerMeta(TestCase):

    def setUp(self):
        test_items = {
            "type": "classifier_meta",
            "intents": ["да", "нет"],
            "classifier": {"type": "external", "classifier": "hello_scenario_classifier"}
        }
        self.filler_meta = ClassifierFillerMeta(test_items)

        self.mock_text_preprocessing_result = Mock()
        self.mock_user = Mock()
        self.mock_user.descriptions = {
            "external_classifiers": ["read_book_or_not_classifier", "hello_scenario_classifier"]}

    @patch.object(ExternalClassifier, "find_best_answer", return_value=[{"answer": "нет", "score": 1.0, "other": False}])
    def test_filler_extract(self, mock_classifier_model):
        """Тест кейз проверяет что мы получаем тот же самый ответ, что вернула модель."""
        expected_res = [{"answer": "нет", "score": 1.0, "other": False}]
        actual_res = self.filler_meta.extract(self.mock_text_preprocessing_result, self.mock_user)
        self.assertEqual(expected_res, actual_res)

    @patch.object(ExternalClassifier, "find_best_answer", return_value=[])
    def test_filler_extract_if_no_model_answer(self, mock_classifier_model):
        """Тест кейз проверяет результат None, если модель не выдала ответ."""
        actual_res = self.filler_meta.extract(self.mock_text_preprocessing_result, self.mock_user)
        self.assertIsNone(actual_res)
