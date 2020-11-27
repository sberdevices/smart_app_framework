from smart_kit.management.base import AppCommand
import os

from core.repositories.file_repository import FileRepository

import json


class CreateCacheCommand(AppCommand):
    """Create cache for normalization results by parsing static"""

    def __init__(self, app_config):
        self._normalize_key = "symbols_for_normalize"
        self._ext = ".json"
        self.app_config = app_config
        self.recognizer_client = app_config.NORMALIZER.with_cache(
            app_config,
            cache_lifetime=float("+inf"),
            verbose=True
        )
        self.recognizer_client.cache.clear()

    def execute(self, *args, **kwargs):
        self.recognizer_client.normalize_sequence(self.items_for_normalized)
        self.recognizer_client.cache.save(os.path.join(self.app_config.REFERENCES_PATH, ".normalization_cache.json"))

    def _collect_items_for_normalized(self, data):
        if hasattr(data, 'items'):
            for key, val in data.items():
                if key == self._normalize_key:
                    yield val
                if isinstance(val, dict):
                    for result in self._collect_items_for_normalized(val):
                        yield result
                elif isinstance(val, list):
                    for item in val:
                        for result in self._collect_items_for_normalized(item):
                            yield result

    @property
    def items_for_normalized(self):
        references_path = self.app_config.REFERENCES_PATH
        items_for_normalized = []
        for r, d, f in os.walk(references_path):
            for file in f:
                if self._ext in file:
                    filename = os.path.join(r, file)
                    rep = FileRepository(filename=filename, loader=json.loads)
                    rep.load()
                    data = rep.data
                    item = self._split_items(self._collect_items_for_normalized(data))
                    items_for_normalized.extend(item)
        return items_for_normalized

    def _split_items(self, items_for_normalized):
        result = []
        for item in items_for_normalized:
            if isinstance(item, dict):
                for key, val in item.items():
                    if isinstance(val, list):
                        result.extend(val)
                    else:
                        result.append(val)
            elif isinstance(item, list):
                result.extend(item)
            else:
                result.append(item)
        return result
