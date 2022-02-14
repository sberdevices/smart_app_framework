from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, AsyncMock

from scenarios.scenario_models.field.field_filler_description import ExternalFieldFillerDescription
from smart_kit.utils.picklable_mock import PicklableMock


class TestExternalFieldFillerDescription(IsolatedAsyncioTestCase):

    async def test_1(self):
        expected = 5
        items = {"filler": "my_key"}
        mock_filler = PicklableMock()
        mock_filler.run = AsyncMock(return_value=expected)

        mock_user = PicklableMock()
        mock_user.descriptions = {"external_field_fillers": {"my_key": mock_filler}}

        filler = ExternalFieldFillerDescription(items)
        result = await filler.extract(None, mock_user)

        self.assertEqual(expected, result)
