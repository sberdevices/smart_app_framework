# coding: utf-8
import unittest

from core.model.queued_objects.limited_queued_hashable_objects import LimitedQueuedHashableObjects

from core.model.queued_objects.limited_queued_hashable_objects_description import \
    LimitedQueuedHashableObjectsDescription


class LimitedQueuedHashableObjectsTest(unittest.TestCase):
    def setUp(self):
        self.descr = LimitedQueuedHashableObjectsDescription(None)

    def test_raw(self):
        last_messages_id = LimitedQueuedHashableObjects([1, 2, 3], self.descr)
        self.assertListEqual(last_messages_id.raw, [1, 2, 3])

    def test_add_true(self):
        last_messages_id = LimitedQueuedHashableObjects([1, 2, 3], self.descr)
        last_messages_id.check(4)
        self.assertListEqual(last_messages_id.raw, [1, 2, 3, 4])

    def test_add_false(self):
        ids = list(range(0, self.descr.max_len))
        last_messages_id = LimitedQueuedHashableObjects(ids, self.descr)
        new_id = self.descr.max_len + 1
        last_messages_id.check(new_id)
        new_ids = ids
        new_ids.pop(0)
        new_ids.append(new_id)
        self.assertListEqual(last_messages_id.raw, new_ids)

    def test_check_true(self):
        last_messages_id = LimitedQueuedHashableObjects([1, 2, 3], self.descr)
        result = last_messages_id.check(1)
        self.assertTrue(result)

    def test_check_false(self):
        last_messages_id = LimitedQueuedHashableObjects([1, 2, 3], self.descr)
        result = last_messages_id.check(4)
        self.assertFalse(result)


class LimitedQueuedHashableObjectsDescriptionTest(unittest.TestCase):
    DEFAULT_MAX_LEN = 10

    def setUp(self):
        self.expected_items = {"max_len": 2}
        self.limited_queued_hashable_objects_description = LimitedQueuedHashableObjectsDescription({"max_len": 2})

    def test_init(self):
        self.assertEqual(self.limited_queued_hashable_objects_description.items, self.expected_items)
        self.assertEqual(self.limited_queued_hashable_objects_description.max_len, 2)

    def test_default_max_len(self):
        limited_queued_hashable_objects_description = LimitedQueuedHashableObjectsDescription({})
        self.assertEqual(limited_queued_hashable_objects_description.max_len,
                         LimitedQueuedHashableObjectsDescription.DEFAULT_MAX_LEN)
