from unittest import TestCase
from unittest.mock import Mock

from scenarios.scenario_models.field.field_filler_description import ExternalFieldFillerDescription


class TestExternalFieldFillerDescription(TestCase):

    def test_1(self):
        expected = 5
        items = {"filler": "my_key"}
        mock_filler = Mock()
        mock_filler.run = Mock(return_value=expected)

        mock_user = Mock()
        mock_user.descriptions = {"external_field_fillers": {"my_key": mock_filler}}

        filler = ExternalFieldFillerDescription(items)
        result = filler.extract(None, mock_user)

        self.assertEqual(expected, result)
