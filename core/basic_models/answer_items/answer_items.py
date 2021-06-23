from typing import Dict, Any, Optional

from core.basic_models.requirement.basic_requirements import Requirement
from core.model.factory import build_factory, factory
from core.model.registered import Registered

answer_items = Registered()
items_factory = build_factory(answer_items)

ANSWER_TO_USER = "ANSWER_TO_USER"


class SdkAnswerItem:
    version: Optional[int]
    id: Optional[str]
    requirement: Requirement

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        items = items or {}
        self.id = id
        self.version = items.get("version", -1)
        self._requirement = items.get("requirement", None)
        self.requirement = self.build_requirement()

    def render(self, nodes: Dict[str, Any]):
        return {}

    @factory(Requirement)
    def build_requirement(self):
        return self._requirement


class TextSdkItem(SdkAnswerItem):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(TextSdkItem, self).__init__(items, id)
        self.text = items['text']


class BubbleText(TextSdkItem):

    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(BubbleText, self).__init__(items, id)
        self.markdown = items.get("markdown", True)

    def render(self, nodes: Dict[str, Any]):
        return {"bubble": {"text": nodes.get(self.text, self.text), "markdown": self.markdown}}


class ItemCard(TextSdkItem):
    def render(self, nodes: Dict[str, Any]):
        return {"card": nodes.get(self.text, self.text)}


class PronounceText(TextSdkItem):
    def render(self, nodes: Dict[str, Any]):
        return {"pronounceText": nodes.get(self.text, self.text)}


class SuggestText(TextSdkItem):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(SuggestText, self).__init__(items, id)
        self.title = items["title"]

    def render(self, nodes: Dict[str, Any]):
        return {"title": nodes.get(self.title, self.title),
                "action": {"text": nodes.get(self.text, self.text), "type": "text"}}


class SuggestDeepLink(SdkAnswerItem):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(SuggestDeepLink, self).__init__(items, id)
        self.title = items["title"]
        self.deep_link = items["deep_link"]

    def render(self, nodes: Dict[str, Any]):
        return {"title": nodes.get(self.title, self.title),
                "action": {"deep_link": nodes.get(self.deep_link, self.deep_link), "type": "deep_link"}}


class RawItem(SdkAnswerItem):
    def __init__(self, items: Dict[str, Any], id: Optional[str] = None):
        super(RawItem, self).__init__(items, id)
        self.key = items["key"]
        self.value = items["value"]

    def render(self, nodes: Dict[str, Any]):
        return {self.key: nodes.get(self.value, self.value)}
