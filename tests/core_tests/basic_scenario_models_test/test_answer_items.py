import unittest

from core.basic_models.answer_items.answer_items import BubbleText, ItemCard, SuggestDeepLink, SuggestText, \
    PronounceText, RawItem


class AnswerItemTest(unittest.TestCase):

    def test_ItemCard(self):
        nodes = {
            "ans": 42
        }
        items = {
            "text": "ans"
        }
        test = ItemCard(items)
        res = test.render(nodes)
        self.assertDictEqual(res, {'card': 42})

    def test_SuggestDeepLink(self):
        nodes = {
            "ans": 42,
            "dl": 24
        }
        items = {
            "deep_link": "dl",
            "title": "ans"
        }
        test = SuggestDeepLink(items)
        res = test.render(nodes)
        self.assertDictEqual(res, {'title': 42, 'action': {'deep_link': 24, 'type': 'deep_link'}})

    def test_SuggestText(self):
        nodes = {
            "ans": 42,
            "text": "text"
        }
        items = {
            "text": "text",
            "title": "ans"
        }
        test = SuggestText(items)
        res = test.render(nodes)
        self.assertDictEqual(res, {'title': 42, 'action': {'text': 'text', 'type': 'text'}})

    def test_SuggestText_no_nodes(self):
        items = {
            "text": "text",
            "title": "ans"
        }
        test = SuggestText(items)
        res = test.render({})
        self.assertDictEqual(res, {'title': "ans", 'action': {'text': 'text', 'type': 'text'}})

    def test_PronounceText(self):
        nodes = {
            "ans": 42
        }
        items = {
            "text": "ans"
        }
        test = PronounceText(items)
        res = test.render(nodes)
        self.assertDictEqual(res, {'pronounceText': 42})


class BubbleItemTest(unittest.TestCase):

    def test_BubbleText(self):
        nodes = {
            "ans": 42
        }
        items = {
            "text": "ans"
        }
        test = BubbleText(items)
        res = test.render(nodes)
        self.assertDictEqual(res, {'bubble': {'text': 42, "markdown": True}})

    def test_Bubble_miss_text(self):
        items = {
            "tsext": "ans"
        }
        self.assertRaises(KeyError, BubbleText, items)

    def test_BubbleText(self):
        nodes = {
            "ans": 42
        }
        items = {
            "text": "ans",
            "markdown": False
        }
        test = BubbleText(items)
        res = test.render(nodes)
        self.assertDictEqual(res, {'bubble': {'text': 42, "markdown": False}})


class RawItemTest(unittest.TestCase):

    def test_finished(self):
        items = {
            "type": "raw",
            "key": "finished",
            "value": "True"
        }
        test = RawItem(items)
        res = test.render({})
        self.assertDictEqual(res, {'finished': "True"})

    def test_Raw_miss_key(self):
        items = {
            "text": "ans"
        }
        self.assertRaises(KeyError, RawItem, items)

    def test_Raw_sophisticated(self):
        nodes = {
            "ans": {
                "emotionId": "oups",
                "ttsAnimation": "sad"
            }
        }
        items = {
            "key": "emotion",
            "value": "ans"
        }
        test = RawItem(items)
        res = test.render(nodes)
        self.assertDictEqual(res, {'emotion': {'emotionId': 'oups', 'ttsAnimation': 'sad'}})