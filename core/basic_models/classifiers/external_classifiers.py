from typing import Dict, Any

from core.basic_models.classifiers.basic_classifiers import classifier_factory
from core.descriptions.smart_updatable_lazy_descriptions import SmartUpdatableLazyDescriptions


class ExternalClassifiers(SmartUpdatableLazyDescriptions):

    def __init__(self, settings: Dict[str, Any]) -> None:
        super(ExternalClassifiers, self).__init__(classifier_factory, settings, ordered=True)
