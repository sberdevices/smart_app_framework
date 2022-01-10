import datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock

from scenarios.scenario_models.field.field_filler_description import RtdmGetPpAndEventsFiller


class TestRtdmGetPpAndEventsFiller(TestCase):

    @patch('requests.request')
    def test1(self, request_fun):
        settings = {"template_settings": {"system_name": "nlpSystem",
                                          "rtdm": {"url": "http://localhost:8088/api/v1/search/epkId", "timeout": 1}}}
        items = {
            "mode": "offerParam,serviceParam"
        }
        filler = RtdmGetPpAndEventsFiller(items)
        user = MagicMock()
        user.settings = settings
        user.message = MagicMock()
        user.message.payload = {"epkId": 34234608109}
        user.message.incremental_id = "5c975471-ecb1-4301-b1ee-a8ddb9de0c3a"
        expected_request = {
            "rqUid": "5c975471-ecb1-4301-b1ee-a8ddb9de0c3a",
            "rqTm": datetime.datetime.utcnow().replace(microsecond=0).isoformat(),
            "systemName": "nlpSystem",
            "channel": "F",
            "epkId": 34234608109,
            "mode": "offerParam,serviceParam"
        }
        res = filler.extract(user=user, text_preprocessing_result=None, params=None)
        request_fun.assert_called_with(url="http://localhost:8088/api/v1/search/epkId", method='post',
                                       json=expected_request,
                                       timeout=1)
        self.assertIsNotNone(res)
