"""Константы классификаторов."""


# Константы любого классификатора, формирующие шаблон ответа
SCORE_KEY = "score"
ANSWER_KEY = "answer"
OTHER_KEY = "other"

# Дополнительные константы для внешних "external" классификаторов
EXTERNAL_CLASSIFIER_BLOCKING_TIMEOUT = 0.2  # Время (в секундах) за которое классификатор должен успеть ответить

# Константы классификатора Intent Recognizer
INTENT_RECOGNIZER_ANSWER_DISTANCE_KEY = "answer_distance"
INTENT_RECOGNIZER_ANSWER_KEY = "answer"
INTENT_RECOGNIZER_OTHER_KEY = "other"

# Параметры, наличие которых обязательно в конфиге любого классификатора
REQUIRED_CONFIG_PARAMS = frozenset(["type"])
