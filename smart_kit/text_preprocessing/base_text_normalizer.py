from typing import Sequence, List

from smart_kit.utils.cache import Cache


class BaseTextNormalizer:
    TEXT_PARAM_NAME = "text"
    PREPROCESS_METHOD = "preprocess"
    CLASSIFY_METHOD = "classify"
    NORMALIZE_METHOD = "normalize"
    CACHE = Cache

    def load_everything(self) -> None:
        raise NotImplementedError

    def with_cache(self, *args, **kwargs) -> 'BaseTextNormalizer':
        raise NotImplementedError

    def normalize_sequence(self, texts: Sequence, batch_size) -> List:
        raise NotImplementedError

    def __call__(self, text: str):
        raise NotImplementedError
