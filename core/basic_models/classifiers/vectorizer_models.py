from core.model.factory import build_factory
from core.model.registered import Registered

vectorizers = Registered()

vectorizer_factory = build_factory(vectorizers)
