import requests
import os
from tqdm import tqdm
from typing import List, Sequence

from smart_kit.text_preprocessing.base_text_normalizer import BaseTextNormalizer
from smart_kit.utils.cache import Cache, ItemExpired


def words_tokenized_set(text):
    return set(text.split(' '))


class NormalizationError(Exception):
    pass


class HttpTextNormalizer(BaseTextNormalizer):

    def __init__(self, url: str, batch_size: int = 128, timeout=10, verbose=False, cache_lifetime=0):
        url = url.rstrip("/") + "/"
        self._preprocess_url = url + HttpTextNormalizer.PREPROCESS_METHOD
        self._classify_url = url + HttpTextNormalizer.CLASSIFY_METHOD
        self._normalize_url = url + HttpTextNormalizer.NORMALIZE_METHOD
        self._batch_size = batch_size
        self._timeout = timeout
        self._verbose = verbose
        self._tqdm_func = tqdm if verbose else (lambda x: x)
        self.set_normalize_mode()

        self.cache = self.CACHE(cache_lifetime)

    @classmethod
    def with_cache(cls, app_config, **kwargs):
        cache_impl = app_config.NORMALIZATION_CACHE
        cls.CACHE = cache_impl
        params = {"url": app_config.NORMALIZER_ADDRESS, "cache_lifetime": app_config.NORMALIZATION_CACHE_TTL}
        params.update(kwargs)
        inst = cls(**params)
        try:
            inst.cache.load(os.path.join(app_config.REFERENCES_PATH, ".normalization_cache.json"))
        except FileNotFoundError:
            pass
        return inst

    def print_current_state(self):
        if self._url == self._preprocess_url:
            print("Выбран режим PREPROCESS_TEXT")
        elif self._url == self._classify_url:
            print("Выбран режим CLASSIFY_TEXT")
        elif self._url == self._normalize_url:
            print("Выбран режим NORMALIZE (только предобработка без аннотаторов)")
        else:
            print("Выбран неизвестный режим")

    def set_preprocess_mode(self):
        self._url = self._preprocess_url
        if self._verbose:
            self.print_current_state()

    def set_classify_mode(self):
        self._url = self._classify_url
        if self._verbose:
            self.print_current_state()

    def set_normalize_mode(self):
        self._url = self._normalize_url
        if self._verbose:
            self.print_current_state()

    def _get_batch(self, sequence: Sequence, n=1) -> Sequence:
        max_ndx = len(sequence)
        for index in self._tqdm_func(range(0, max_ndx, n)):
            yield sequence[index: min(index + n, max_ndx)]

    def _normalize_batch(self, batch: Sequence) -> List:
        response = requests.post(self._url, json=[{HttpTextNormalizer.TEXT_PARAM_NAME: el} for el in batch],
                                 timeout=self._timeout)
        response.raise_for_status()
        result = response.json()
        for item in result:
            self.cache[item["message"]["original_text"]] = item["message"]
        return result

    def normalize_sequence(self, texts: Sequence, batch_size=None) -> List:
        normalized_texts = []
        batch_generator = self._get_batch(texts, batch_size or self._batch_size)
        for batch in batch_generator:
            normalized_texts.extend(self._normalize_batch(batch))
        return normalized_texts

    def __call__(self, text: str):
        try:
            return self.cache[text]
        except (KeyError, ItemExpired):
            pass

        batch = self._normalize_batch([text])
        if len(batch) == 0:
            raise NormalizationError("Empty Message Received")

        answer = batch[0]

        if "message" not in answer:
            raise NormalizationError(f"Malformed Message Received: {batch}")

        return answer["message"]

    def load_everything(self) -> None:
        pass
