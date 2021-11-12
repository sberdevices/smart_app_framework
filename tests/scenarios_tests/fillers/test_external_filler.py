from unittest import IsolatedAsyncioTestCase
from unittest.mock import Mock, AsyncMock

from scenarios.scenario_models.field.field_filler_description import ExternalFieldFillerDescription


class TestExternalFieldFillerDescription(IsolatedAsyncioTestCase):

    async def test_1(self):
        expected = 5
        items = {"filler": "my_key"}
        mock_filler = Mock()
        mock_filler.run = AsyncMock(return_value=expected)

        mock_user = Mock()
        mock_user.descriptions = {"external_field_fillers": {"my_key": mock_filler}}

        filler = ExternalFieldFillerDescription(items)
        result = await filler.extract(None, mock_user)

        self.assertEqual(expected, result)
