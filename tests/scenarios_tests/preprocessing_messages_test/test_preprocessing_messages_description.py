import unittest

from scenarios.user.preprocessing_messages.preprocessing_messages_description import \
    PreprocessingMessagesDescription


class PreprocessingMessagesDescriptionTest(unittest.TestCase):

    def test_description(self):
        items = {"messages": 5, "lifetime": 600}
        description = PreprocessingMessagesDescription(items)
        self.assertEqual(description.max_message_count, 5)
        self.assertEqual(description.lifetime, 600)
