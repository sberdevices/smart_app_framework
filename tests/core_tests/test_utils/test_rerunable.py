from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock

from core.utils.rerunable import Rerunable


class HandledException(Exception):
    pass


class AllFailedException(Exception):
    pass


class CustomException(Exception):
    pass


class RerunableOne(Rerunable):
    def __init__(self, try_count):
        super(RerunableOne, self).__init__({"try_count": try_count})
        self._on_prepare_mock = Mock()

    @property
    async def _handled_exception(self):
        return HandledException

    async def _on_prepare(self):
        self._on_prepare_mock()

    async def _on_all_tries_fail(self):
        raise AllFailedException

    async def run(self, *args, **kwargs):
        return await self._run(*args, **kwargs)


class TestRerunable(IsolatedAsyncioTestCase):
    def setUp(self):
        self.try_count = 2
        self.rerunable = RerunableOne(self.try_count)
        self.expected_value = Mock()
        self.param = Mock()
        self.param1 = {"param1_name": Mock()}

    async def test_pass(self):
        self.action = Mock()
        await self.rerunable.run(self.action, self.param, **self.param1)
        self.action.assert_called_once_with(self.param, **self.param1)

    # TODO: починить тест
    async def test_wrong_exception(self):
        self.action = Mock(side_effect=CustomException())
        with self.assertRaises(CustomException) as context:
            await self.rerunable.run(self.action, self.param, **self.param1)
        self.action.assert_called_once_with(self.param, **self.param1)

    async def test_all_retry_failed(self):
        self.action = Mock(side_effect=HandledException())
        with self.assertRaises(AllFailedException) as context:
            await self.rerunable.run(self.action, self.param, **self.param1)
        self.action.assert_called_with(self.param, **self.param1)
        self.assertEqual(self.action.call_count, self.try_count)

    async def test_first_try_failed(self):
        self.param = Mock()
        self.param1 = {"param1_name": Mock()}
        self.action = Mock(side_effect=[HandledException(), self.expected_value])
        result = await self.rerunable.run(self.action, self.param, **self.param1)
        self.action.assert_called_with(self.param, **self.param1)
        self.assertEqual(self.action.call_count, self.try_count)
        self.assertEqual(result, self.expected_value)

    async def test_first_try_ok(self):
        self.action = Mock(return_value=self.expected_value)
        result = await self.rerunable.run(self.action, self.param, **self.param1)
        self.action.assert_called_once_with(self.param, **self.param1)
        self.assertEqual(result, self.expected_value)
